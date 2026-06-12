"""Cross-source duplicate detection.

The unit of analysis is one recall event per row. Each source produces its own
row, but the same real-world event may appear in multiple sources (e.g. an FDA
recall that the FSA UK also issues a PRIN for). We link them via fingerprint
(firm + product text + country, normalized) without merging.
"""
from __future__ import annotations
import sqlite3


def find_duplicate_groups(conn: sqlite3.Connection) -> list[list[str]]:
    """Return groups of alert ids that share a fingerprint across sources."""
    cur = conn.execute("""
        SELECT fingerprint, GROUP_CONCAT(id) AS ids, COUNT(*) AS n,
               COUNT(DISTINCT source_id) AS n_sources
        FROM alerts
        GROUP BY fingerprint
        HAVING n > 1 AND n_sources > 1
    """)
    groups = []
    for row in cur:
        groups.append(row["ids"].split(","))
    return groups


def report_duplicates(conn: sqlite3.Connection) -> dict:
    groups = find_duplicate_groups(conn)
    cur = conn.execute("SELECT COUNT(*) FROM alerts")
    total = cur.fetchone()[0]
    return {
        "total_alerts": total,
        "duplicate_groups": len(groups),
        "duplicates_count": sum(len(g) - 1 for g in groups),
        "sample_groups": groups[:5],
    }
