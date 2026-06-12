"""Strategic pair selection for LLM labeling.

Selects ~300 pairs from a 500-alert stratified sample, in four categories:

1. same-severity pairs (hardest cases — model must decide between similars)
2. adjacent-severity pairs (moderate difficulty)
3. polar pairs (easy validation — high vs low)
4. cross-source pairs (robustness — FDA vs FSA UK at same severity)

Avoids pairs that are obvious duplicates (same firm + same product).
"""
from __future__ import annotations
import hashlib
import random
import sqlite3
from datetime import datetime
from itertools import combinations

from .improved_fingerprint import event_fingerprint


SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def _pair_id(a_id: str, b_id: str) -> str:
    """Stable, order-independent pair identifier."""
    ids = sorted([a_id, b_id])
    return hashlib.md5(f"{ids[0]}::{ids[1]}".encode()).hexdigest()[:16]


def _alert_event_fp(a: sqlite3.Row) -> str:
    return event_fingerprint(
        a["recalling_firm"],
        a["hazard_specific"],
        a["product_category"],
        a["event_initiation_date"],
    )


def _is_near_duplicate(a: sqlite3.Row, b: sqlite3.Row) -> bool:
    """Skip pairs where both alerts look like the same underlying event.

    Three signals:
      1. Same raw fingerprint (firm + product + country).
      2. Same event_fingerprint — likely same event across sources.
      3. Same firm AND same first 50 chars of product description.
    """
    if a["fingerprint"] == b["fingerprint"]:
        return True
    if _alert_event_fp(a) == _alert_event_fp(b):
        return True
    same_firm = (a["recalling_firm"] or "").lower() == (b["recalling_firm"] or "").lower()
    same_prod = (a["product_description"] or "").lower()[:50] == (b["product_description"] or "").lower()[:50]
    return same_firm and same_prod


def load_sample(conn: sqlite3.Connection, sample_name: str) -> list[sqlite3.Row]:
    cur = conn.execute("""
        SELECT a.* FROM alerts a
        JOIN sample_members sm ON sm.alert_id = a.id
        WHERE sm.sample_name = ?
    """, (sample_name,))
    return cur.fetchall()


def select_pairs(
    conn: sqlite3.Connection,
    sample_name: str,
    n_same_severity: int = 100,
    n_adjacent: int = 100,
    n_polar: int = 50,
    n_cross_source: int = 50,
    seed: int = 42,
) -> list[dict]:
    """Select strategic pairs. Returns a list of pair dicts and persists them."""
    rng = random.Random(seed)
    alerts = load_sample(conn, sample_name)

    by_severity: dict[str, list[sqlite3.Row]] = {"high": [], "medium": [], "low": []}
    for a in alerts:
        sev = a["severity_normalized"]
        if sev in by_severity:
            by_severity[sev].append(a)

    selected: list[tuple[sqlite3.Row, sqlite3.Row, str]] = []
    seen_pair_ids: set[str] = set()

    def add_pair(a, b, category):
        pid = _pair_id(a["id"], b["id"])
        if pid in seen_pair_ids or _is_near_duplicate(a, b):
            return False
        seen_pair_ids.add(pid)
        selected.append((a, b, category))
        return True

    # Category 1: same-severity pairs — hardest discrimination.
    same_target_per_severity = n_same_severity // 3
    for sev in ("high", "medium", "low"):
        pool = by_severity[sev]
        rng.shuffle(pool)
        added = 0
        for a, b in combinations(pool, 2):
            if add_pair(a, b, f"same_severity_{sev}"):
                added += 1
                if added >= same_target_per_severity:
                    break

    # Category 2: adjacent-severity pairs.
    adj_pairs_targets = {
        ("high", "medium"): n_adjacent // 2,
        ("medium", "low"): n_adjacent - (n_adjacent // 2),
    }
    for (sev_hi, sev_lo), target in adj_pairs_targets.items():
        candidates = [(a, b) for a in by_severity[sev_hi] for b in by_severity[sev_lo]]
        rng.shuffle(candidates)
        added = 0
        for a, b in candidates:
            if add_pair(a, b, f"adjacent_{sev_hi}_{sev_lo}"):
                added += 1
                if added >= target:
                    break

    # Category 3: polar pairs (high vs low).
    candidates = [(a, b) for a in by_severity["high"] for b in by_severity["low"]]
    rng.shuffle(candidates)
    added = 0
    for a, b in candidates:
        if add_pair(a, b, "polar_high_low"):
            added += 1
            if added >= n_polar:
                break

    # Category 4: cross-source pairs at same severity (FDA vs FSA UK).
    target_per_sev = n_cross_source // 2
    for sev in ("high", "medium"):
        fda = [a for a in by_severity[sev] if a["source_id"] == "fda_enforcement"]
        fsa = [a for a in by_severity[sev] if a["source_id"] == "fsa_uk"]
        candidates = [(a, b) for a in fda for b in fsa]
        rng.shuffle(candidates)
        added_in_sev = 0
        for a, b in candidates:
            if add_pair(a, b, f"cross_source_{sev}"):
                added_in_sev += 1
                if added_in_sev >= target_per_sev:
                    break

    # Persist.
    now = datetime.utcnow().isoformat(timespec="seconds")
    conn.execute("DELETE FROM labeling_pairs WHERE sample_name = ?", (sample_name,))
    rows = []
    for a, b, cat in selected:
        pid = _pair_id(a["id"], b["id"])
        conn.execute(
            "INSERT INTO labeling_pairs (pair_id, sample_name, alert_a_id, alert_b_id, pair_category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, sample_name, a["id"], b["id"], cat, now),
        )
        rows.append({"pair_id": pid, "alert_a_id": a["id"], "alert_b_id": b["id"], "category": cat})
    conn.commit()
    return rows


def breakdown(conn: sqlite3.Connection, sample_name: str) -> dict:
    cur = conn.execute(
        "SELECT pair_category, COUNT(*) AS n FROM labeling_pairs WHERE sample_name = ? GROUP BY pair_category ORDER BY pair_category",
        (sample_name,),
    )
    return {r["pair_category"]: r["n"] for r in cur}
