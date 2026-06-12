"""Export all labeling pairs (with alert text) for manual LLM labeling in Cursor chat.

Usage:
  # All 299 pairs for labeling_v3
  python3 scripts/export_labeling_pairs.py --sample labeling_v3 \\
    --out data/labeling_pairs_v3_for_llm.json

  # Pilot 10 (spread across categories)
  python3 scripts/export_labeling_pairs.py --sample labeling_v3 -n 10 \\
    --out data/labeling_pairs_pilot10_for_llm.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.prompts import render_alert_as_text


def _row_to_alert(row: dict) -> dict:
    return {
        "id": row["id"],
        "text": render_alert_as_text(row),
        "severity_normalized": row["severity_normalized"],
        "source": row["source_id"],
        "israel_relevance_flag": bool(row.get("israel_relevance_flag")),
    }


def main():
    parser = argparse.ArgumentParser(description="Export pairs for LLM labeling")
    parser.add_argument("--sample", default="labeling_v3")
    parser.add_argument(
        "-n", "--n-pairs", type=int, default=None,
        help="If set, export only N pairs spread across categories (pilot mode)",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    conn = db.connect()
    cur = conn.execute(
        """
        SELECT pair_id, alert_a_id, alert_b_id, pair_category
        FROM labeling_pairs WHERE sample_name = ?
        ORDER BY pair_category, pair_id
        """,
        (args.sample,),
    )
    all_pairs = cur.fetchall()
    if not all_pairs:
        raise SystemExit(f"No pairs found for sample_name={args.sample!r}")

    picked = list(all_pairs)
    if args.n_pairs is not None:
        by_cat: dict[str, list] = {}
        for p in all_pairs:
            by_cat.setdefault(p["pair_category"], []).append(p)
        picked = []
        cats = sorted(by_cat.keys())
        while len(picked) < args.n_pairs and any(by_cat.values()):
            for cat in cats:
                if by_cat[cat] and len(picked) < args.n_pairs:
                    picked.append(by_cat[cat].pop(0))

    out_list = []
    for p in picked:
        a = dict(conn.execute("SELECT * FROM alerts WHERE id = ?", (p["alert_a_id"],)).fetchone())
        b = dict(conn.execute("SELECT * FROM alerts WHERE id = ?", (p["alert_b_id"],)).fetchone())
        out_list.append({
            "pair_index": len(out_list) + 1,
            "pair_id": p["pair_id"],
            "category": p["pair_category"],
            "alert_a": _row_to_alert(a),
            "alert_b": _row_to_alert(b),
        })

    meta = {
        "sample_name": args.sample,
        "pair_count": len(out_list),
        "export_note": "Use with LLM_LABELING_CHAT_PASTE.md — system prompt in src/labeling/prompts.py",
    }

    payload = {"meta": meta, "pairs": out_list}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(out_list)} pairs to {out_path}")
    print("Categories:", sorted({p["category"] for p in out_list}))


if __name__ == "__main__":
    main()
