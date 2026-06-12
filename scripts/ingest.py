"""CLI to run ingestion across all configured sources."""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Allow running as a script from project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import run_all
from src.collectors import COLLECTORS


def main():
    parser = argparse.ArgumentParser(description="Ingest food safety alerts")
    parser.add_argument("--sources", nargs="+", default=list(COLLECTORS.keys()),
                        help=f"Sources to run (default: all). Available: {', '.join(COLLECTORS.keys())}")
    parser.add_argument("--days", type=int, default=730,
                        help="Look-back window in days (default: 730 = 2 years)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max records per source (default: no limit)")
    args = parser.parse_args()

    since = datetime.utcnow() - timedelta(days=args.days)
    results = run_all(args.sources, since=since, limit_per_source=args.limit)

    print("\n=== Ingestion summary ===")
    for r in results:
        if r.get("error"):
            print(f"  [{r['source_id']}] ERROR: {r['error']}")
        else:
            print(f"  [{r['source_id']}] fetched={r['fetched']} inserted={r['inserted']} updated={r['updated']}")


if __name__ == "__main__":
    main()
