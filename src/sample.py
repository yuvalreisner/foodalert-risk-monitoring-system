"""Stratified sampling for the labeling set.

Primary stratum: severity_normalized (high/medium/low).
Secondary balance: source_id, with a soft cap per (severity, source) cell.
"""
from __future__ import annotations
import random
import sqlite3


def stratified_sample(
    conn: sqlite3.Connection,
    n: int = 100,
    seed: int = 42,
    sample_name: str = "labeling_v1",
) -> dict:
    """Pick `n` alerts stratified by severity, balanced across sources.

    Returns a dict with counts per stratum and the list of selected alert ids.
    Records the selection in `sample_members` for traceability.
    """
    rng = random.Random(seed)

    # Step 1: bucket by severity.
    target_per_severity = {
        "high": n // 3 + (n % 3 > 0),    # 34 of 100
        "medium": n // 3 + (n % 3 > 1),  # 33 of 100
        "low": n // 3,                   # 33 of 100
    }

    selected_ids: list[str] = []
    breakdown: dict[str, dict[str, int]] = {}

    for severity, target in target_per_severity.items():
        cur = conn.execute(
            "SELECT id, source_id FROM alerts WHERE severity_normalized = ?",
            (severity,),
        )
        rows = cur.fetchall()
        # Bucket by source within the severity stratum.
        by_source: dict[str, list[str]] = {}
        for r in rows:
            by_source.setdefault(r["source_id"], []).append(r["id"])

        # Round-robin pick from sources to balance.
        per_source_target = target // max(1, len(by_source))
        remainder = target - per_source_target * len(by_source)
        chosen_in_stratum: list[str] = []
        for src, ids in by_source.items():
            rng.shuffle(ids)
            take = min(per_source_target, len(ids))
            chosen_in_stratum.extend(ids[:take])
            by_source[src] = ids[take:]  # leftovers for the remainder pass.

        # Distribute the remainder from sources that still have slack.
        remainder_pool = [i for ids in by_source.values() for i in ids]
        rng.shuffle(remainder_pool)
        chosen_in_stratum.extend(remainder_pool[:max(0, target - len(chosen_in_stratum))])

        selected_ids.extend(chosen_in_stratum)
        breakdown[severity] = {"target": target, "actual": len(chosen_in_stratum),
                                "by_source": {s: sum(1 for i in chosen_in_stratum if i in (by_source.get(s, []) + [c for c in chosen_in_stratum]))
                                              for s in by_source}}

    # Persist selection.
    conn.execute("DELETE FROM sample_members WHERE sample_name = ?", (sample_name,))
    for aid in selected_ids:
        sev_row = conn.execute("SELECT severity_normalized FROM alerts WHERE id = ?", (aid,)).fetchone()
        stratum = sev_row["severity_normalized"] if sev_row else None
        conn.execute(
            "INSERT INTO sample_members (sample_name, alert_id, stratum) VALUES (?, ?, ?)",
            (sample_name, aid, stratum),
        )
    conn.commit()

    return {
        "sample_name": sample_name,
        "n_selected": len(selected_ids),
        "n_target": n,
        "breakdown": breakdown,
        "selected_ids": selected_ids,
    }
