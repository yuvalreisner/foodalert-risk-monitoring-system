"""Score all alerts in the DB with the trained Bi-Encoder + baselines.

Step 7 — Production scoring.

Outputs:
  - data/all_alert_scores.json
  - DB table: alert_scores (created if absent, replaced on each run)

Baselines computed alongside the model score:
  - severity_baseline: Class I=1.0, Class II=0.6, Class III=0.2, etc.
  - tfidf_score: cosine similarity to a "high-danger" query (requires scikit-learn)

Usage:
  python3 scripts/score_all_alerts.py
  python3 scripts/score_all_alerts.py --no-tfidf    # skip if sklearn not installed
  python3 scripts/score_all_alerts.py --batch-size 32
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
from src.models.bi_encoder import BiEncoderRiskModel

DEFAULT_CHECKPOINT = Path("models/bi_encoder_labeling_v3/best_model.pt")
DEFAULT_OUT = Path("data/all_alert_scores.json")

_SEV_MAP = {
    "class i":  1.0, "class ii": 0.6, "class iii": 0.2,
    "fafa":     1.0, "aa":       0.9, "prin":      0.6,
    "high":     1.0, "medium":   0.6, "low":       0.2,
}

DANGER_QUERY = (
    "listeria salmonella allergen undeclared severe illness death outbreak "
    "hospitalization Class I recall nationwide ready-to-eat pathogen "
    "E.coli botulinum vulnerable children elderly anaphylaxis"
)


def _sev_baseline(raw: str | None) -> float:
    if not raw:
        return 0.5
    r = raw.lower()
    for key, val in _SEV_MAP.items():
        if key in r:
            return val
    return 0.5


@torch.no_grad()
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--no-tfidf", action="store_true", help="Skip TF-IDF baseline")
    args = ap.parse_args()

    print(f"Loading checkpoint: {args.checkpoint}")
    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    backbone  = ckpt["backbone"]
    max_length = ckpt["max_length"]
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}  Backbone: {backbone}")

    tokenizer = AutoTokenizer.from_pretrained(backbone)
    # Detect architecture from checkpoint shape and load accordingly.
    score_head_shape = ckpt["model_state"]["score_head.weight"].shape
    has_hidden = "hidden.weight" in ckpt["model_state"]
    if has_hidden:
        hidden_size = score_head_shape[1]
        model = BiEncoderRiskModel(backbone=backbone, hidden_size=hidden_size)
        model.load_state_dict(ckpt["model_state"])
        print(f"  Architecture: 768→{hidden_size}→1 (new)")
    else:
        # Old checkpoint: BERT → Dropout → Linear(768→1). Load with a shim.
        import torch.nn as nn
        from transformers import AutoModel

        class _OldArch(nn.Module):
            def __init__(self):
                super().__init__()
                self.encoder   = AutoModel.from_pretrained(backbone)
                self.dropout   = nn.Dropout(0.1)
                self.score_head = nn.Linear(768, 1)

            def encode_text(self, input_ids, attention_mask):
                out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                pooled = out.last_hidden_state[:, 0, :]
                return self.score_head(self.dropout(pooled)).squeeze(-1)

        model = _OldArch()
        model.load_state_dict(ckpt["model_state"])
        print("  Architecture: 768→1 (old checkpoint — re-train recommended)")
    model.to(device).eval()

    conn = db.connect()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY source_published_date DESC"
    ).fetchall()
    conn.close()
    print(f"Loaded {len(rows)} alerts from DB")

    texts = [render_alert_as_text(dict(r)) for r in rows]

    # ── Bi-Encoder scoring ────────────────────────────────────────────────
    print("Scoring with Bi-Encoder...")
    raw_scores: list[float] = []
    for i in range(0, len(texts), args.batch_size):
        if i % 2000 == 0:
            print(f"  {i}/{len(texts)}", flush=True)
        batch = texts[i : i + args.batch_size]
        enc = tokenizer(
            batch, truncation=True, max_length=max_length,
            padding=True, return_tensors="pt",
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        s = model.encode_text(enc["input_ids"], enc["attention_mask"])
        raw_scores.extend(s.cpu().tolist())
    print(f"  {len(rows)}/{len(rows)} done")

    # ── Baselines ─────────────────────────────────────────────────────────
    sev_scores = [_sev_baseline(dict(r)["severity_raw"]) for r in rows]

    tfidf_scores = [0.0] * len(rows)
    if not args.no_tfidf:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            print("Computing TF-IDF baseline...")
            vec = TfidfVectorizer(max_features=20000, sublinear_tf=True)
            mat = vec.fit_transform(texts)
            q   = vec.transform([DANGER_QUERY])
            tfidf_scores = cosine_similarity(q, mat).flatten().tolist()
        except ImportError:
            print("  scikit-learn not installed — skipping TF-IDF (use --no-tfidf to silence)")

    # ── Percentile rank (global, over all 18k) ────────────────────────────
    import numpy as np
    arr   = np.array(raw_scores)
    ranks = arr.argsort().argsort()
    pct_ranks = (ranks / max(len(arr) - 1, 1)).tolist()

    # ── Correlations ──────────────────────────────────────────────────────
    try:
        from scipy.stats import spearmanr
        r_sev,   p_sev   = spearmanr(raw_scores, sev_scores)
        r_tfidf, p_tfidf = spearmanr(raw_scores, tfidf_scores)
        print(f"\nSpearman(Bi-Encoder, severity_raw_baseline) = {r_sev:.3f}  p={p_sev:.3g}")
        print(f"Spearman(Bi-Encoder, TF-IDF)               = {r_tfidf:.3f}  p={p_tfidf:.3g}")
    except ImportError:
        print("\nscipy not available — skipping Spearman correlation")
        r_sev = r_tfidf = None

    # ── Assemble results ──────────────────────────────────────────────────
    results = []
    for r, score, pct, sev, tfidf in zip(
        rows, raw_scores, pct_ranks, sev_scores, tfidf_scores
    ):
        row = dict(r)
        results.append({
            "alert_id":              row["id"],
            "source_id":             row["source_id"],
            "source_published_date": row["source_published_date"],
            "title":                 (row.get("title") or "")[:120],
            "product_description":   (row.get("product_description") or "")[:120],
            "hazard_specific":       row.get("hazard_specific") or "",
            "severity_raw":          row.get("severity_raw") or "",
            "severity_normalized":   row.get("severity_normalized") or "",
            "distribution_countries": row.get("distribution_countries") or "",
            "bi_encoder_score":      round(score, 5),
            "bi_encoder_percentile": round(pct, 4),
            "severity_baseline":     sev,
            "tfidf_score":           round(tfidf, 5),
        })

    results.sort(key=lambda x: -x["bi_encoder_score"])

    # ── Top-10 preview ────────────────────────────────────────────────────
    print("\nTop 10 alerts by Bi-Encoder score:")
    for r in results[:10]:
        label = (r["title"] or r["product_description"])[:60]
        print(
            f"  {r['bi_encoder_score']:+.4f}  pct={r['bi_encoder_percentile']:.2f}"
            f"  {r['severity_raw']:12s}  {r['source_id']:20s}  {label}"
        )

    # ── Save JSON ─────────────────────────────────────────────────────────
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "n_alerts": len(results),
            "backbone": backbone,
            "checkpoint": str(args.checkpoint),
            "spearman_vs_severity_baseline": round(r_sev, 4) if r_sev else None,
            "spearman_vs_tfidf":             round(r_tfidf, 4) if r_tfidf else None,
        },
        "scores": results,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {args.out}")

    # ── Write to DB ───────────────────────────────────────────────────────
    conn = db.connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_scores (
            alert_id               TEXT PRIMARY KEY,
            bi_encoder_score       REAL,
            bi_encoder_percentile  REAL,
            severity_baseline      REAL,
            tfidf_score            REAL,
            scored_at              TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("DELETE FROM alert_scores")
    conn.executemany(
        "INSERT INTO alert_scores "
        "(alert_id, bi_encoder_score, bi_encoder_percentile, severity_baseline, tfidf_score) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (
                r["alert_id"], r["bi_encoder_score"], r["bi_encoder_percentile"],
                r["severity_baseline"], r["tfidf_score"],
            )
            for r in results
        ],
    )
    conn.commit()
    conn.close()
    print(f"Written {len(results)} rows → alert_scores table in DB")


if __name__ == "__main__":
    main()
