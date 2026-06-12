"""Improved cross-source event fingerprinting.

The original fingerprint (firm + product + country) failed to link the same
real-world event across sources because:
  - country differs (USA vs UK)
  - firm naming conventions differ (Inc / Ltd / LLC / Co suffixes)
  - product descriptions are written differently by each agency

This module computes a more lenient fingerprint that bases identity on:
  - normalized firm name (corporate suffix stripped, lower, whitespace normalized)
  - hazard_specific keyword (Listeria, Salmonella, undeclared peanut, etc.)
  - product_category (Dairy, Meat & Poultry, etc.)
  - approximate event date (year-quarter, so close-in-time events match)

Two records sharing all four are very likely the same real-world event.
"""
from __future__ import annotations
import hashlib
import re
from datetime import datetime


_CORPORATE_SUFFIXES = [
    r"\binc\b", r"\bllc\b", r"\bltd\b", r"\blimited\b", r"\bco\b",
    r"\bcorp\b", r"\bcorporation\b", r"\bgmbh\b", r"\bs\.?\s?a\.?\b",
    r"\bbv\b", r"\bplc\b", r"\bllp\b", r"\blp\b", r"\bpty\b", r"\bcompany\b",
]


def normalize_firm(firm: str | None) -> str:
    if not firm:
        return ""
    name = firm.lower()
    # Strip punctuation
    name = re.sub(r"[^\w\s]", " ", name)
    # Strip corporate suffixes
    for suffix in _CORPORATE_SUFFIXES:
        name = re.sub(suffix, " ", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    # Keep only first 4 tokens — handles "Acme Foods" vs "Acme Foods (UK)"
    tokens = name.split()
    return " ".join(tokens[:4])


def _quarter_bucket(date_str: str | None) -> str:
    """Bucket a date to year-quarter (e.g. '2024-Q3'). Same quarter = same event."""
    if not date_str:
        return "unknown"
    try:
        d = datetime.fromisoformat(date_str[:10])
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}"
    except ValueError:
        return date_str[:7]  # fallback: YYYY-MM


def event_fingerprint(
    firm: str | None,
    hazard_specific: str | None,
    product_category: str | None,
    event_date: str | None,
) -> str:
    """Cross-source event identity hash."""
    components = [
        normalize_firm(firm),
        (hazard_specific or "").lower().strip(),
        (product_category or "").lower().strip(),
        _quarter_bucket(event_date),
    ]
    text = "|".join(components)
    return hashlib.md5(text.encode()).hexdigest()[:16]
