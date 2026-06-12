"""Bradley-Terry MLE from pairwise LLM labels.

Fits one model per dimension (severity, likelihood, exposure) using choix ILSR.
Comparisons: if LLM winner is A, alert_a beats alert_b; if B, the reverse.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime

import choix
import numpy as np

DIMENSIONS = ("severity", "likelihood", "exposure")


@dataclass
class BTFitResult:
    dimension: str
    n_items: int
    n_comparisons: int
    n_components: int
    items_scored: int
    scores: dict[str, float]  # alert_id -> BT strength (log-scale, mean-centered)


def load_comparisons(
    conn: sqlite3.Connection,
    dimension: str,
    sample_name: str = "labeling_v3",
    model: str = "claude-sonnet-4-6",
    order_variant: str = "A_first",
) -> list[tuple[str, str]]:
    """Return (winner_alert_id, loser_alert_id) for each labeled pair."""
    cur = conn.execute(
        """
        SELECT lp.alert_a_id, lp.alert_b_id, ll.winner
        FROM llm_labels ll
        JOIN labeling_pairs lp ON lp.pair_id = ll.pair_id
        WHERE ll.dimension = ?
          AND ll.model = ?
          AND ll.order_variant = ?
          AND lp.sample_name = ?
        """,
        (dimension, model, order_variant, sample_name),
    )
    out: list[tuple[str, str]] = []
    for a_id, b_id, winner in cur:
        if winner == "A":
            out.append((a_id, b_id))
        elif winner == "B":
            out.append((b_id, a_id))
    return out


def _connected_components(n_items: int, comparisons_idx: list[tuple[int, int]]) -> int:
    parent = list(range(n_items))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for w, l in comparisons_idx:
        union(w, l)
    return len({find(i) for i in range(n_items)})


def fit_bradley_terry(
    comparisons: list[tuple[str, str]],
    alpha: float = 1.0,
    max_iter: int = 100,
) -> BTFitResult:
    """Fit BT strengths. alpha: choix L2 regularization (default 1.0)."""
    if not comparisons:
        raise ValueError("No comparisons to fit")

    items = sorted({x for pair in comparisons for x in pair})
    idx = {aid: i for i, aid in enumerate(items)}
    data = [(idx[w], idx[l]) for w, l in comparisons]
    n_components = _connected_components(len(items), data)

    params = choix.ilsr_pairwise(
        n_items=len(items),
        data=data,
        alpha=alpha,
        max_iter=max_iter,
    )
    # Mean-center for interpretability (BT is identifiable up to additive constant)
    params = params - float(np.mean(params))
    scores = {items[i]: float(params[i]) for i in range(len(items))}
    return BTFitResult(
        dimension="",
        n_items=len(items),
        n_comparisons=len(comparisons),
        n_components=n_components,
        items_scored=len(scores),
        scores=scores,
    )


def fit_all_dimensions(
    conn: sqlite3.Connection,
    sample_name: str = "labeling_v3",
    model: str = "claude-sonnet-4-6",
    order_variant: str = "A_first",
    alpha: float = 1.0,
) -> dict[str, BTFitResult]:
    results = {}
    for dim in DIMENSIONS:
        comps = load_comparisons(conn, dim, sample_name, model, order_variant)
        r = fit_bradley_terry(comps, alpha=alpha)
        r.dimension = dim
        results[dim] = r
    return results


def persist_scores(
    conn: sqlite3.Connection,
    results: dict[str, BTFitResult],
    sample_name: str,
    model: str,
    fitted_at: str | None = None,
) -> int:
    """Write scores to bt_scores table. Returns rows written."""
    fitted_at = fitted_at or datetime.utcnow().isoformat(timespec="seconds")
    conn.execute("DELETE FROM bt_scores WHERE sample_name = ? AND label_model = ?", (sample_name, model))
    n = 0
    for dim, res in results.items():
        for alert_id, score in res.scores.items():
            conn.execute(
                """
                INSERT INTO bt_scores
                (alert_id, sample_name, dimension, score, label_model, n_comparisons_in_fit, fitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (alert_id, sample_name, dim, score, model, res.n_comparisons, fitted_at),
            )
            n += 1
    conn.commit()
    return n
