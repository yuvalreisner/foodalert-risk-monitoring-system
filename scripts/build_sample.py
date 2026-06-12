"""CLI to build the stratified labeling sample from the alerts DB."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.sample import stratified_sample
from src.dedup import report_duplicates


def main():
    parser = argparse.ArgumentParser(description="Build stratified labeling sample")
    parser.add_argument("-n", "--n-samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", default="labeling_v1")
    args = parser.parse_args()

    conn = db.connect()
    db.init_schema(conn)

    print("=== Dedup report ===")
    print(json.dumps(report_duplicates(conn), indent=2, default=str))

    print(f"\n=== Building stratified sample (n={args.n_samples}) ===")
    result = stratified_sample(conn, n=args.n_samples, seed=args.seed, sample_name=args.name)

    breakdown = {k: v for k, v in result["breakdown"].items()}
    summary = {
        "sample_name": result["sample_name"],
        "n_selected": result["n_selected"],
        "n_target": result["n_target"],
        "breakdown": breakdown,
    }
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
