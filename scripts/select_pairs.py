"""CLI to select pairs from the labeling sample for LLM judging."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.pair_selection import select_pairs, breakdown


def main():
    parser = argparse.ArgumentParser(description="Select pairs for LLM labeling")
    parser.add_argument("--sample", default="labeling_v2",
                        help="Name of the stratified sample to draw pairs from")
    parser.add_argument("--same", type=int, default=100, help="# same-severity pairs")
    parser.add_argument("--adjacent", type=int, default=100, help="# adjacent-severity pairs")
    parser.add_argument("--polar", type=int, default=50, help="# polar (high vs low) pairs")
    parser.add_argument("--cross-source", type=int, default=50, help="# cross-source pairs")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    conn = db.connect()
    db.init_schema(conn)

    pairs = select_pairs(
        conn,
        sample_name=args.sample,
        n_same_severity=args.same,
        n_adjacent=args.adjacent,
        n_polar=args.polar,
        n_cross_source=args.cross_source,
        seed=args.seed,
    )

    print(f"\n=== Selected {len(pairs)} pairs from sample '{args.sample}' ===")
    print("\nBreakdown by category:")
    print(json.dumps(breakdown(conn, args.sample), indent=2))


if __name__ == "__main__":
    main()
