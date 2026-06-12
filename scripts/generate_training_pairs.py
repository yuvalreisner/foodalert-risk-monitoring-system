"""Step 5: Generate synthetic Bi-Encoder training pairs from BT composite scores.

Three-way split (per Lev Muchnik feedback 2026-06-08):
  train 70% — used for gradient updates
  val   15% — used for early stopping and model selection
  test  15% — evaluated ONCE at the very end (never used for decisions)

Usage:
  python3 scripts/generate_training_pairs.py --write-db
  python3 scripts/generate_training_pairs.py --test-frac 0.15 --val-frac 0.15 --write-db
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.training_pairs import (
    DEFAULT_MODEL,
    DEFAULT_SAMPLE,
    DEFAULT_TEST_FRAC,
    DEFAULT_VAL_FRAC,
    build_training_dataset,
    export_pairs_csv,
    persist_split_and_pairs,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic training pairs from BT composite")
    parser.add_argument("--sample", default=DEFAULT_SAMPLE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--test-frac", type=float, default=DEFAULT_TEST_FRAC,
                        help="Fraction held out as final test (never used for model selection)")
    parser.add_argument("--val-frac", type=float, default=DEFAULT_VAL_FRAC,
                        help="Fraction used for validation / early stopping")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--allow-ties", action="store_true", help="Keep pairs with equal composite (random winner)")
    parser.add_argument(
        "--out-json",
        default="data/synthetic_training_pairs.json",
        help="Full dataset JSON (meta + split + pairs with text)",
    )
    parser.add_argument(
        "--out-dir",
        default="data/exports/training_pairs",
        help="Directory for train/test CSV files",
    )
    parser.add_argument("--write-db", action="store_true", help="Persist to SQLite tables")
    args = parser.parse_args()

    conn = db.connect()
    db.init_schema(conn)

    dataset = build_training_dataset(
        conn,
        sample_name=args.sample,
        label_model=args.model,
        test_frac=args.test_frac,
        val_frac=args.val_frac,
        seed=args.seed,
        skip_ties=not args.allow_ties,
    )

    if args.write_db:
        persist_split_and_pairs(conn, dataset)

    conn.close()

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    out_dir = Path(args.out_dir)
    export_pairs_csv(dataset["pairs"]["train"], out_dir / "train_pairs.csv")
    export_pairs_csv(dataset["pairs"]["val"],   out_dir / "val_pairs.csv")
    export_pairs_csv(dataset["pairs"]["test"],  out_dir / "test_pairs.csv")

    m = dataset["meta"]
    print("=== Synthetic training pairs (step 5) — three-way split ===\n")
    print(f"Sample:        {m['sample_name']}")
    print(f"BT model:      {m['label_model']}")
    print(f"Scored alerts: {m['n_scored_alerts']}")
    print(f"Train alerts:  {m['n_train_alerts']}  →  {m['n_train_pairs']:,} pairs")
    print(f"Val alerts:    {m['n_val_alerts']}  →  {m['n_val_pairs']:,} pairs  (model selection)")
    print(f"Test alerts:   {m['n_test_alerts']}  →  {m['n_test_pairs']:,} pairs  (final eval only)")
    print(f"Split:         {int(m['val_frac']*100)}% val / {int(m['test_frac']*100)}% test, seed={m['seed']}")
    print(f"Label rule:    {m['label_rule']}")
    print(f"\nWrote JSON:  {out_json}")
    print(f"Wrote CSV:   {out_dir}/train_pairs.csv")
    print(f"             {out_dir}/val_pairs.csv")
    print(f"             {out_dir}/test_pairs.csv")
    if args.write_db:
        print("Wrote DB:    training_split_members, synthetic_training_pairs")


if __name__ == "__main__":
    main()
