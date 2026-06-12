"""One-time setup: create a trimmed operational DB from the full 23k-alert DB.

Keeps only the last 13 months of alerts + their scores.
The trimmed DB is what gets committed to GitHub and updated daily.

Usage (run once from project root):
    python3 scripts/trim_db.py

Output: data/alerts.db is replaced in-place with the trimmed version.
The original full DB is backed up to data/alerts_full_backup.db.
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "alerts.db"
BACKUP_PATH = PROJECT_ROOT / "data" / "alerts_full_backup.db"
KEEP_MONTHS = 13


def main() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found")
        sys.exit(1)

    cutoff = (date.today() - timedelta(days=KEEP_MONTHS * 30)).isoformat()
    print(f"Keeping alerts from {cutoff} onwards ({KEEP_MONTHS} months)")

    # Count before
    conn = sqlite3.connect(DB_PATH)
    total_before = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    keep = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE source_published_date >= ?", (cutoff,)
    ).fetchone()[0]
    conn.close()

    print(f"Current DB: {total_before:,} alerts  →  will keep {keep:,} alerts")
    print(f"Backup: {BACKUP_PATH}")

    confirm = input("Proceed? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    # Backup first
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backed up to {BACKUP_PATH}")

    # Trim in-place
    conn = sqlite3.connect(DB_PATH)

    # Delete old alert_scores (FK cascade doesn't help here since FK may be off)
    conn.execute(
        "DELETE FROM alert_scores WHERE alert_id IN ("
        "  SELECT id FROM alerts WHERE source_published_date < ?"
        ")",
        (cutoff,),
    )
    conn.execute(
        "DELETE FROM alerts WHERE source_published_date < ?", (cutoff,)
    )
    conn.commit()
    conn.execute("VACUUM")

    total_after = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    conn.close()

    size_mb = DB_PATH.stat().st_size / 1_048_576
    print(f"Done. {total_after:,} alerts remain. DB size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
