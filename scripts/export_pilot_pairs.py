"""Export a small pilot set of pairs to a JSON file the LLM can label.

Selects N pairs spread across the 8 pair categories for diversity.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.prompts import render_alert_as_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="labeling_v2")
    parser.add_argument("-n", "--n-pairs", type=int, default=10)
    parser.add_argument("--out", default="data/pilot_pairs.json")
    args = parser.parse_args()

    conn = db.connect()

    # Get one or two pairs from each category, up to n_pairs total.
    cur = conn.execute("""
        SELECT pair_id, alert_a_id, alert_b_id, pair_category
        FROM labeling_pairs WHERE sample_name = ?
        ORDER BY pair_category, pair_id
    """, (args.sample,))
    all_pairs = cur.fetchall()

    # Spread across categories
    by_cat = {}
    for p in all_pairs:
        by_cat.setdefault(p["pair_category"], []).append(p)

    picked = []
    cats = list(by_cat.keys())
    while len(picked) < args.n_pairs and any(by_cat.values()):
        for cat in cats:
            if by_cat[cat] and len(picked) < args.n_pairs:
                picked.append(by_cat[cat].pop(0))

    # Render each pair with full alert text.
    pilot = []
    for p in picked:
        a = dict(conn.execute("SELECT * FROM alerts WHERE id = ?", (p["alert_a_id"],)).fetchone())
        b = dict(conn.execute("SELECT * FROM alerts WHERE id = ?", (p["alert_b_id"],)).fetchone())
        pilot.append({
            "pair_id": p["pair_id"],
            "category": p["pair_category"],
            "alert_a": {
                "id": a["id"],
                "text": render_alert_as_text(a),
                "severity_normalized": a["severity_normalized"],
                "source": a["source_id"],
            },
            "alert_b": {
                "id": b["id"],
                "text": render_alert_as_text(b),
                "severity_normalized": b["severity_normalized"],
                "source": b["source_id"],
            },
        })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(pilot, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(pilot)} pilot pairs to {args.out}")
    print("Categories included:", sorted(set(p["category"] for p in pilot)))


if __name__ == "__main__":
    main()
