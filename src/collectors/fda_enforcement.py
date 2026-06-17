"""openFDA food enforcement reports collector.

Endpoint: https://api.fda.gov/food/enforcement.json
Docs:     https://open.fda.gov/apis/food/enforcement/
"""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime
from typing import Iterator

from .base import BaseCollector, make_retry_session

ENDPOINT = "https://api.fda.gov/food/enforcement.json"
PAGE_SIZE = 1000  # openFDA hard cap is 1000.


class FDAEnforcementCollector(BaseCollector):
    source_id = "fda_enforcement"

    def fetch_raw(self, since: datetime | None = None, limit: int | None = None) -> Iterator[dict]:
        skip = 0
        fetched = 0
        session = make_retry_session()
        while True:
            page_size = min(PAGE_SIZE, (limit - fetched) if limit else PAGE_SIZE)
            if page_size <= 0:
                break
            # openFDA's Lucene parser rejects URL-encoded `:` `[` `]`, so we build
            # the search query manually and only let requests encode the values it owns.
            url = f"{ENDPOINT}?limit={page_size}&skip={skip}"
            if since:
                date_str = since.strftime("%Y%m%d")
                today_str = datetime.utcnow().strftime("%Y%m%d")
                url += f"&search=report_date:[{date_str}+TO+{today_str}]"
            r = session.get(url, timeout=30)
            if r.status_code == 404:
                # openFDA returns 404 when results exhausted.
                return
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            if not results:
                return
            for rec in results:
                yield rec
                fetched += 1
                if limit and fetched >= limit:
                    return
            if len(results) < page_size:
                return
            skip += page_size

    def normalize(self, raw: dict) -> dict:
        record_id = raw.get("recall_number", "")
        title = self._build_title(raw)
        description = raw.get("reason_for_recall", "")
        product_desc = raw.get("product_description", "")

        return {
            "id": f"fda_enforcement::{record_id}",
            "source_id": self.source_id,
            "source_record_id": record_id,
            "fingerprint": _make_fingerprint(raw.get("recalling_firm"), product_desc, raw.get("country")),
            "record_url": f"https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts?search_api_fulltext={record_id}",
            "ingestion_date": datetime.utcnow().isoformat(timespec="seconds"),
            "source_published_date": _parse_fda_date(raw.get("report_date")),
            "event_initiation_date": _parse_fda_date(raw.get("recall_initiation_date")),
            "event_status": (raw.get("status") or "").lower() or None,
            "origin_country": raw.get("country"),
            "distribution_countries": json.dumps(_extract_distribution(raw.get("distribution_pattern", ""))),
            "israel_relevance_flag": _is_israel_relevant(raw),
            "recalling_firm": raw.get("recalling_firm"),
            "brand_names": json.dumps([]),
            "product_description": product_desc,
            "product_category": None,  # filled by enrichment step later
            "hazard_category": None,
            "hazard_specific": None,
            "severity_raw": raw.get("classification"),
            "severity_normalized": _normalize_fda_class(raw.get("classification")),
            "population_at_risk": None,
            "illness_count_reported": None,
            "title": title,
            "description": description,
            "reason_for_recall": raw.get("reason_for_recall"),
        }

    @staticmethod
    def _build_title(raw: dict) -> str:
        firm = str(raw.get("recalling_firm") or "")
        cls = str(raw.get("classification") or "")
        product = str(raw.get("product_description") or "")[:80]
        return f"{firm} — {cls} — {product}".strip(" —")


def _parse_fda_date(date_str: str | None) -> str | None:
    """openFDA dates are YYYYMMDD strings."""
    if not date_str:
        return None
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


def _normalize_fda_class(classification: str | None) -> str | None:
    if not classification:
        return None
    c = classification.lower()
    if "class i" in c and "ii" not in c and "iii" not in c:
        return "high"
    if "class ii" in c and "iii" not in c:
        return "medium"
    if "class iii" in c:
        return "low"
    return None


def _make_fingerprint(firm: str | None, product: str | None, country: str | None) -> str:
    text = " ".join([(firm or "").lower(), (product or "").lower()[:120], (country or "").lower()])
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.md5(text.encode()).hexdigest()


def _extract_distribution(distribution_pattern: str) -> list:
    """Best-effort extraction of country/state codes from free-text distribution."""
    if not distribution_pattern:
        return []
    # The field is usually US states, sometimes "Nationwide" or country names.
    return [distribution_pattern]  # Keep full text — truncation causes Israel detection to fail in display.


def _is_israel_relevant(raw: dict) -> int:
    blob = json.dumps(raw, default=str).lower()
    return 1 if "israel" in blob else 0
