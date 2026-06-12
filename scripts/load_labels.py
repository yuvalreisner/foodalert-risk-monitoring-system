"""Load LLM labels from a JSON file into the llm_labels table.

Accepts nested or flat records per pair:

  Nested:  "severity": {"winner": "A", "reasoning": "..."}
  Flat:    "severity_winner": "A", "severity_reasoning": "..."
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db

DIMENSIONS = ["severity", "likelihood", "exposure"]


def get_dimension(item: dict, dim: str) -> dict | None:
    """Return {winner, reasoning} from nested or flat keys."""
    block = item.get(dim)
    if isinstance(block, dict) and block.get("winner") in ("A", "B"):
        return {
            "winner": block["winner"],
            "reasoning": block.get("reasoning", "") or "",
        }
    winner = item.get(f"{dim}_winner")
    if winner in ("A", "B"):
        return {
            "winner": winner,
            "reasoning": item.get(f"{dim}_reasoning", "") or "",
        }
    return None


def normalize_records(labels: list) -> list[dict]:
    """Convert flat labels to nested format for export."""
    out = []
    for item in labels:
        if not item.get("pair_id"):
            continue
        row = {"pair_id": item["pair_id"]}
        if item.get("category"):
            row["category"] = item["category"]
        if item.get("pair_index") is not None:
            row["pair_index"] = item["pair_index"]
        for dim in DIMENSIONS:
            block = get_dimension(item, dim)
            if block:
                row[dim] = block
        out.append(row)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to JSON label file")
    parser.add_argument("--model", default="claude-opus-4-7-in-chat",
                        help="Model identifier for provenance")
    parser.add_argument("--order-variant", default="A_first",
                        help="Order variant: A_first or B_first")
    parser.add_argument(
        "--write-normalized",
        metavar="PATH",
        help="Also write nested JSON (e.g. data/llm_labels_v3_nested.json)",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        labels = json.load(f)

    if args.write_normalized:
        normalized = normalize_records(labels)
        out_path = Path(args.write_normalized)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)
        print(f"Wrote nested format to {out_path} ({len(normalized)} pairs)")

    conn = db.connect()
    db.init_schema(conn)

    inserted = 0
    skipped = 0
    now = datetime.utcnow().isoformat(timespec="seconds")

    for item in labels:
        pair_id = item.get("pair_id")
        if not pair_id:
            skipped += 1
            continue
        # Verify pair exists
        row = conn.execute(
            "SELECT 1 FROM labeling_pairs WHERE pair_id = ?", (pair_id,)
        ).fetchone()
        if not row:
            print(f"  WARN: pair_id={pair_id} not in labeling_pairs, skipping")
            skipped += 1
            continue

        for dim in DIMENSIONS:
            block = get_dimension(item, dim)
            if not block:
                print(f"  WARN: missing {dim} for {pair_id}")
                continue
            winner = block["winner"]
            reasoning = block["reasoning"]
            conn.execute(
                """INSERT OR REPLACE INTO llm_labels
                   (pair_id, dimension, order_variant, winner, reasoning, model, labeled_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (pair_id, dim, args.order_variant, winner, reasoning, args.model, now),
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"\n=== Loaded {inserted} labels across {len(labels)} pairs (skipped {skipped}) ===")


if __name__ == "__main__":
    main()
