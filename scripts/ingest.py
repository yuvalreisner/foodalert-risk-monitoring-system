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

# Safety buffer: even in smart mode, never look back less than this many days.
# Guards against a source that was silent yesterday publishing 3 weeks late.
SMART_MIN_DAYS = 30


def _last_seen_per_source(sources: list[str]) -> dict[str, datetime]:
    """Return the most recent source_published_date per source from the DB."""
    from src import db
    conn = db.connect()
    result = {}
    for src in sources:
        row = conn.execute(
            "SELECT MAX(source_published_date) FROM alerts WHERE source_id = ?",
            (src,),
        ).fetchone()
        if row and row[0]:
            try:
                last = datetime.fromisoformat(row[0])
                result[src] = last
            except ValueError:
                pass
    conn.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="Ingest food safety alerts")
    parser.add_argument("--sources", nargs="+", default=list(COLLECTORS.keys()),
                        help=f"Sources to run (default: all). Available: {', '.join(COLLECTORS.keys())}")
    parser.add_argument("--days", type=int, default=730,
                        help="Look-back window in days (default: 730 = 2 years)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max records per source (default: no limit)")
    parser.add_argument("--smart", action="store_true",
                        help=f"Use per-source last-seen date from DB as since, "
                             f"with a minimum of {SMART_MIN_DAYS} days back. "
                             "Prevents gaps when a source goes silent for weeks.")
    args = parser.parse_args()

    if args.smart:
        last_seen = _last_seen_per_source(args.sources)
        min_since = datetime.utcnow() - timedelta(days=SMART_MIN_DAYS)
        # Run each source with its own since date
        all_results = []
        for src in args.sources:
            per_src_since = last_seen.get(src)
            if per_src_since is None or per_src_since > min_since:
                since = min_since
            else:
                since = per_src_since
            print(f"[{src}] smart since: {since.date()} "
                  f"(last seen: {last_seen.get(src, 'never')})")
            results = run_all([src], since=since, limit_per_source=args.limit)
            all_results.extend(results)
    else:
        since = datetime.utcnow() - timedelta(days=args.days)
        all_results = run_all(args.sources, since=since, limit_per_source=args.limit)

    print("\n=== Ingestion summary ===")
    for r in all_results:
        if r.get("error"):
            print(f"  [{r['source_id']}] ERROR: {r['error']}")
        else:
            print(f"  [{r['source_id']}] fetched={r['fetched']} inserted={r['inserted']} updated={r['updated']}")


if __name__ == "__main__":
    main()
