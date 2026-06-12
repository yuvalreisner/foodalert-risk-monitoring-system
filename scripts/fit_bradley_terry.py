"""Fit Bradley-Terry models per dimension and persist scores to SQLite.

Usage:
  python3 scripts/fit_bradley_terry.py
  python3 scripts/fit_bradley_terry.py --sample labeling_v3 --model claude-sonnet-4-6
  python3 scripts/fit_bradley_terry.py --export data/bt_scores_labeling_v3.json
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.bradley_terry import (
    DIMENSIONS,
    fit_all_dimensions,
    load_comparisons,
    persist_scores,
)


def build_composite(conn, sample_name: str, model: str, fitted_at: str) -> int:
    """Equal-weight average of severity/likelihood/exposure BT scores (1/3 each)."""
    conn.execute(
        "DELETE FROM bt_scores WHERE sample_name = ? AND dimension = 'composite' AND label_model = ?",
        (sample_name, model),
    )
    cur = conn.execute(
        """
        SELECT alert_id, AVG(score) AS composite
        FROM bt_scores
        WHERE sample_name = ? AND label_model = ? AND dimension IN ('severity', 'likelihood', 'exposure')
        GROUP BY alert_id
        HAVING COUNT(DISTINCT dimension) = 3
        """,
        (sample_name, model),
    )
    n = 0
    for alert_id, composite in cur:
        conn.execute(
            """
            INSERT INTO bt_scores
            (alert_id, sample_name, dimension, score, label_model, n_comparisons_in_fit, fitted_at)
            VALUES (?, ?, 'composite', ?, ?, NULL, ?)
            """,
            (alert_id, sample_name, float(composite), model, fitted_at),
        )
        n += 1
    conn.commit()
    return n


def main():
    parser = argparse.ArgumentParser(description="Fit Bradley-Terry per dimension")
    parser.add_argument("--sample", default="labeling_v3")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--order-variant", default="A_first")
    parser.add_argument("--alpha", type=float, default=1.0, help="choix L2 regularization")
    parser.add_argument("--export", help="Optional JSON export path")
    parser.add_argument("--no-composite", action="store_true", help="Skip equal-weight composite")
    args = parser.parse_args()

    conn = db.connect()
    db.init_schema(conn)

    # Ensure bt_scores table exists on older DBs
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS bt_scores (
            alert_id TEXT NOT NULL,
            sample_name TEXT NOT NULL,
            dimension TEXT NOT NULL,
            score REAL NOT NULL,
            label_model TEXT NOT NULL,
            n_comparisons_in_fit INTEGER,
            fitted_at TEXT NOT NULL,
            PRIMARY KEY (alert_id, sample_name, dimension, label_model)
        );
        """
    )
    conn.commit()

    sample_n = conn.execute(
        "SELECT COUNT(*) FROM sample_members WHERE sample_name = ?", (args.sample,)
    ).fetchone()[0]

    print(f"=== Bradley-Terry fit | sample={args.sample} | model={args.model} ===\n")
    print(f"Sample members in DB: {sample_n}")

    results = fit_all_dimensions(
        conn,
        sample_name=args.sample,
        model=args.model,
        order_variant=args.order_variant,
        alpha=args.alpha,
    )

    fitted_at = datetime.utcnow().isoformat(timespec="seconds")
    rows = persist_scores(conn, results, args.sample, args.model, fitted_at)

    for dim in DIMENSIONS:
        r = results[dim]
        comps = load_comparisons(conn, dim, args.sample, args.model, args.order_variant)
        scores = list(r.scores.values())
        print(f"\n{dim.upper()}")
        print(f"  Comparisons: {r.n_comparisons}")
        print(f"  Alerts with BT score: {r.items_scored} (in comparison graph)")
        print(f"  Graph components: {r.n_components}" + (" (OK: connected)" if r.n_components == 1 else " (WARNING: disconnected)"))
        if scores:
            print(f"  Score range: {min(scores):.3f} … {max(scores):.3f} (mean-centered)")

    composite_n = 0
    if not args.no_composite:
        composite_n = build_composite(conn, args.sample, args.model, fitted_at)
        print(f"\nCOMPOSITE (equal 1/3 weights)")
        print(f"  Alerts with all 3 dimensions + composite: {composite_n}")

    missing = conn.execute(
        """
        SELECT COUNT(*) FROM sample_members sm
        LEFT JOIN bt_scores bt ON bt.alert_id = sm.alert_id
          AND bt.sample_name = sm.sample_name
          AND bt.dimension = 'severity' AND bt.label_model = ?
        WHERE sm.sample_name = ? AND bt.alert_id IS NULL
        """,
        (args.model, args.sample),
    ).fetchone()[0]
    if missing:
        print(f"\nNote: {missing} of {sample_n} sample alerts have no BT score (never appeared in a labeled pair).")

    print(f"\n=== Saved {rows} rows to bt_scores (+ composite: {composite_n}) ===")

    if args.export:
        export = {
            "sample_name": args.sample,
            "label_model": args.model,
            "fitted_at": fitted_at,
            "dimensions": {},
        }
        for dim in list(DIMENSIONS) + (["composite"] if not args.no_composite else []):
            cur = conn.execute(
                """
                SELECT alert_id, score FROM bt_scores
                WHERE sample_name = ? AND dimension = ? AND label_model = ?
                ORDER BY score DESC
                """,
                (args.sample, dim, args.model),
            )
            export["dimensions"][dim] = [
                {"alert_id": r[0], "score": r[1]} for r in cur
            ]
        out = Path(args.export)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False)
        print(f"Exported rankings to {out}")

    conn.close()


if __name__ == "__main__":
    main()
