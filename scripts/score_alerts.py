"""Score individual alerts with a trained Bi-Encoder (step 7 preview).

Usage:
  python3 scripts/score_alerts.py --split test
  python3 scripts/score_alerts.py --split train --out data/bi_encoder_scores_test.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.prompts import render_alert_as_text
from src.labeling.training_pairs import DEFAULT_MODEL, DEFAULT_SAMPLE
from src.models.bi_encoder import BiEncoderRiskModel

DEFAULT_CHECKPOINT = Path("models/bi_encoder_labeling_v3/best_model.pt")


@torch.no_grad()
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--split", choices=("train", "test"), default="test")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    backbone = ckpt["backbone"]
    max_length = ckpt["max_length"]

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(backbone)
    model = BiEncoderRiskModel(backbone=backbone)
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()

    conn = db.connect()
    rows = conn.execute(
        """
        SELECT a.*, t.composite, t.split
        FROM training_split_members t
        JOIN alerts a ON a.id = t.alert_id
        WHERE t.sample_name = ? AND t.label_model = ? AND t.split = ?
        ORDER BY t.composite DESC
        """,
        (args.sample, args.model, args.split),
    ).fetchall()
    conn.close()

    texts = [render_alert_as_text(dict(r)) for r in rows]
    scores: list[float] = []

    for i in range(0, len(texts), args.batch_size):
        batch = texts[i : i + args.batch_size]
        enc = tokenizer(
            batch,
            truncation=True,
            max_length=max_length,
            padding=True,
            return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        s = model.encode_text(enc["input_ids"], enc["attention_mask"])
        scores.extend(s.cpu().tolist())

    out_rows = []
    for r, score in zip(rows, scores):
        out_rows.append(
            {
                "alert_id": r["id"],
                "bi_encoder_score": score,
                "bt_composite": r["composite"],
                "source_id": r["source_id"],
                "severity_normalized": r["severity_normalized"],
                "recalling_firm": r["recalling_firm"],
            }
        )

    # Rank correlation with BT composite
    import numpy as np
    from numpy.linalg import LinAlgError

    bt = np.array([x["bt_composite"] for x in out_rows])
    pred = np.array([x["bi_encoder_score"] for x in out_rows])
    try:
        from scipy.stats import spearmanr
        rho, pval = spearmanr(pred, bt)
        corr_msg = f"Spearman(pred, BT composite) = {rho:.3f} (p={pval:.4g})"
    except (ImportError, LinAlgError):
        corr_msg = "scipy not installed — skip correlation"

    print(f"Scored {len(out_rows)} alerts ({args.split} split)")
    print(corr_msg)
    print("Top 5 by model score:")
    for row in sorted(out_rows, key=lambda x: -x["bi_encoder_score"])[:5]:
        print(f"  {row['bi_encoder_score']:.3f}  BT={row['bt_composite']:.4f}  {row['alert_id']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"split": args.split, "scores": out_rows, "correlation_note": corr_msg}, f, indent=2)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
