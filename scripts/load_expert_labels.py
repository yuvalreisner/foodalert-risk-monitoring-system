"""Load expert labels from the JSON file exported by expert_review.html.

Expected JSON structure (flat key-value):
  {
    "pair_<pair_id>_severity":   "A"|"B",
    "pair_<pair_id>_likelihood": "A"|"B",
    "pair_<pair_id>_exposure":   "A"|"B",
    "pair_<pair_id>_reasoning":  "...",     # free text
    "pair_<pair_id>_reflection": "...",     # free text (post-LLM reveal)
    "overall_factors":           "...",     # general thoughts
    "hidden_factors":            "...",
    "llm_disagreement":          "...",
    "notes":                     "..."
  }

Usage:
  python3 scripts/load_expert_labels.py --input expert_review_2026-05-18.json --expert "Matan Shiner"
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db

DIMENSIONS = ("severity", "likelihood", "exposure")
PAIR_FIELD_RE = re.compile(r"^pair_([a-f0-9]{16})_(severity|likelihood|exposure|reasoning|reflection)$")
GENERAL_FIELDS = {"overall_factors", "hidden_factors", "llm_disagreement", "notes"}


def parse_export(data: dict) -> tuple[dict, dict]:
    """Split the flat export into per-pair entries and general feedback."""
    by_pair: dict[str, dict] = {}
    general: dict[str, str] = {}

    for key, value in data.items():
        m = PAIR_FIELD_RE.match(key)
        if m:
            pid, field = m.group(1), m.group(2)
            by_pair.setdefault(pid, {})[field] = value
        elif key in GENERAL_FIELDS:
            general[key] = value
        else:
            print(f"  (unknown field — skipping: {key})")

    return by_pair, general


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to expert JSON file")
    parser.add_argument("--expert", required=True,
                        help='Expert identifier (e.g. "Matan Shiner" or "Noga Naor")')
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    by_pair, general = parse_export(data)
    print(f"\nParsed {len(by_pair)} pairs and {len(general)} general fields")

    conn = db.connect()
    db.init_schema(conn)

    now = datetime.utcnow().isoformat(timespec="seconds")
    inserted = 0
    skipped = 0

    for pair_id, fields in by_pair.items():
        # Verify the pair exists
        row = conn.execute(
            "SELECT pair_id FROM labeling_pairs WHERE pair_id = ?", (pair_id,)
        ).fetchone()
        if not row:
            print(f"  WARN: pair_id {pair_id} not in labeling_pairs — skipping")
            skipped += 1
            continue

        reasoning = fields.get("reasoning", "")
        reflection = fields.get("reflection", "")
        # Combine reasoning + reflection as notes
        notes_parts = []
        if reasoning:
            notes_parts.append(f"[blind] {reasoning}")
        if reflection:
            notes_parts.append(f"[post-LLM] {reflection}")
        notes = "\n\n".join(notes_parts)

        for dim in DIMENSIONS:
            winner = fields.get(dim)
            if winner not in ("A", "B"):
                print(f"  WARN: pair {pair_id} / {dim} — invalid winner {winner!r}")
                continue
            conn.execute(
                """INSERT OR REPLACE INTO expert_labels
                   (pair_id, dimension, expert_name, winner, notes, labeled_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (pair_id, dim, args.expert, winner, notes, now),
            )
            inserted += 1

    # Save general feedback as a side file (no schema for it yet)
    if general:
        meta_path = Path("data") / f"expert_general_{args.expert.replace(' ', '_')}_{now[:10]}.json"
        meta_path.parent.mkdir(exist_ok=True)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"expert": args.expert, "labeled_at": now, "answers": general}, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved general feedback to: {meta_path}")

    conn.commit()
    conn.close()
    print(f"\n=== Loaded {inserted} expert labels for {args.expert} (skipped {skipped} pairs) ===")


if __name__ == "__main__":
    main()
