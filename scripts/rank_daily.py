"""Step 7b — Daily MOH ranking pipeline.

Reads alert_scores + alerts from DB, applies a rolling time window,
re-ranks within the window, classifies Critical / High / Medium / Low,
and outputs a JSON digest + HTML report.

Percentile thresholds (within the rolling window):
  Critical  top  5%  (window_percentile ≥ 0.95)
  High      5–20%    (window_percentile ≥ 0.80)
  Medium   20–50%    (window_percentile ≥ 0.50)
  Low      bottom 50%

Usage:
  python3 scripts/rank_daily.py                       # last 30 days, today
  python3 scripts/rank_daily.py --window 60
  python3 scripts/rank_daily.py --date 2026-05-01     # as-of a specific date
  python3 scripts/rank_daily.py --out reports/digest_today
  python3 scripts/rank_daily.py --min-tier high       # omit medium from output
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import db

CRITICAL_THRESHOLD = 0.95
HIGH_THRESHOLD     = 0.80
MEDIUM_THRESHOLD   = 0.50

_TIER_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_HTML = """\
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>FoodSafe Intelligence — דיגסט {date}</title>
<style>
  body      {{ font-family: Arial, sans-serif; max-width: 980px; margin: 0 auto; padding: 20px; color: #222; }}
  h1        {{ color: #1a1a2e; margin-bottom: 4px; }}
  h2        {{ margin-top: 28px; margin-bottom: 6px; }}
  p.meta    {{ color: #666; font-size: 13px; margin-top: 2px; }}
  .critical {{ border-left: 5px solid #c0392b; background: #fdf3f3; padding: 12px 14px; margin: 8px 0; border-radius: 4px; }}
  .high     {{ border-left: 5px solid #d35400; background: #fef6ee; padding: 12px 14px; margin: 8px 0; border-radius: 4px; }}
  .medium   {{ border-left: 5px solid #d4ac0d; background: #fefcee; padding: 12px 14px; margin: 8px 0; border-radius: 4px; }}
  .badge    {{ display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 8px; }}
  .b-c      {{ background: #c0392b; color: #fff; }}
  .b-h      {{ background: #d35400; color: #fff; }}
  .b-m      {{ background: #d4ac0d; color: #fff; }}
  .b-il     {{ background: #1a5276; color: #fff; }}
  .score    {{ font-family: monospace; font-size: 13px; color: #333; }}
  .field    {{ color: #555; font-size: 13px; }}
  .title    {{ font-weight: bold; font-size: 15px; }}
  .israel   {{ border-left: 5px solid #1a5276; background: #eaf0fb; padding: 12px 14px; margin: 8px 0; border-radius: 4px; }}
</style>
</head>
<body>
<h1>FoodSafe Intelligence — דיגסט {date}</h1>
<p class="meta">
  חלון: {window_days} ימים ({window_start} – {date}) &nbsp;|&nbsp;
  {n_in_window} ריקולים בחלון &nbsp;|&nbsp;
  <strong style="color:#c0392b">{n_critical} קריטיים</strong> &nbsp;
  <strong style="color:#d35400">{n_high} גבוהים</strong> &nbsp;
  <strong style="color:#d4ac0d">{n_medium} בינוניים</strong> &nbsp;
  <strong style="color:#1a5276">🇮🇱 {n_israel} רלוונטיים לישראל</strong>
</p>
<hr>
{sections}
<hr>
<p class="meta" style="font-size:11px">הופק על-ידי FoodSafe Intelligence · {generated_at}</p>
</body>
</html>
"""

_CARD = """\
<div class="{cls}">
  <span class="title">{title}</span>
  <span class="badge b-{b}">{tier_he}</span><br>
  <span class="score">{score:+.4f}</span>
  <span class="field">אחוזון בחלון: {pct:.0%} &nbsp;|&nbsp; {source_id} &nbsp;|&nbsp; {date_str}</span><br>
  <span class="field">סיכון: {hazard} &nbsp;|&nbsp; חומרה: {severity_raw}</span><br>
  <span class="field">הפצה: {distribution}</span>
</div>"""

_CARD_IL = """\
<div class="israel">
  <span class="title">{title}</span>
  <span class="badge b-il">🇮🇱 ישראל</span>
  <span class="badge b-{b}">{tier_he}</span><br>
  <span class="score">{score:+.4f}</span>
  <span class="field">אחוזון בחלון: {pct:.0%} &nbsp;|&nbsp; {source_id} &nbsp;|&nbsp; {date_str}</span><br>
  <span class="field">סיכון: {hazard} &nbsp;|&nbsp; חומרה: {severity_raw}</span><br>
  <span class="field">מקור הרלוונטיות: {israel_reason}</span><br>
  <span class="field">הפצה: {distribution}</span>
</div>"""


def _rank_within_window(alerts: list[dict]) -> list[dict]:
    n = len(alerts)
    if n == 0:
        return alerts
    order = sorted(range(n), key=lambda i: alerts[i]["bi_encoder_score"])
    for rank, idx in enumerate(order):
        alerts[idx]["window_percentile"] = rank / max(n - 1, 1)
    return alerts


def _tier(pct: float) -> tuple[str, str]:
    if pct >= CRITICAL_THRESHOLD:
        return "critical", "קריטי"
    if pct >= HIGH_THRESHOLD:
        return "high", "גבוה"
    if pct >= MEDIUM_THRESHOLD:
        return "medium", "בינוני"
    return "low", "נמוך"


def _dist_text(raw: str | None) -> str:
    if not raw:
        return "לא צוין"
    try:
        lst = json.loads(raw) if raw.strip().startswith("[") else [raw]
        return ", ".join(str(x) for x in lst[:4])
    except Exception:
        return raw[:80]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=30)
    ap.add_argument("--date", default=None, help="Reference date YYYY-MM-DD")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--min-tier", choices=["critical", "high", "medium", "low"], default="medium")
    args = ap.parse_args()

    ref_date     = date.fromisoformat(args.date) if args.date else date.today()
    window_start = ref_date - timedelta(days=args.window)

    conn = db.connect()
    try:
        rows = conn.execute(
            """
            SELECT s.alert_id, s.bi_encoder_score, s.bi_encoder_percentile,
                   s.severity_baseline, s.tfidf_score,
                   a.source_id, a.source_published_date, a.title,
                   a.product_description, a.hazard_specific, a.hazard_category,
                   a.severity_raw, a.severity_normalized, a.distribution_countries,
                   a.recalling_firm, a.origin_country, a.israel_relevance_flag
            FROM alert_scores s
            JOIN alerts a ON a.id = s.alert_id
            WHERE a.source_published_date >= ? AND a.source_published_date <= ?
            ORDER BY s.bi_encoder_score DESC
            """,
            (window_start.isoformat(), ref_date.isoformat()),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"DB error: {exc}")
        print("Run scripts/score_all_alerts.py first to populate alert_scores.")
        sys.exit(1)
    conn.close()

    alerts = [dict(r) for r in rows]
    print(f"Window {window_start} – {ref_date}: {len(alerts)} alerts")

    if not alerts:
        print("No alerts in window.")
        sys.exit(0)

    alerts = _rank_within_window(alerts)

    for a in alerts:
        tier, tier_he = _tier(a["window_percentile"])
        a["tier"] = tier
        a["tier_he"] = tier_he

    n_critical = sum(1 for a in alerts if a["tier"] == "critical")
    n_high     = sum(1 for a in alerts if a["tier"] == "high")
    n_medium   = sum(1 for a in alerts if a["tier"] == "medium")
    n_israel   = sum(1 for a in alerts if a.get("israel_relevance_flag"))
    print(f"  Critical: {n_critical}  High: {n_high}  Medium: {n_medium}  Israel: {n_israel}")

    shown = [a for a in alerts if _TIER_ORDER[a["tier"]] <= _TIER_ORDER[args.min_tier]]

    out_prefix = args.out or Path(f"reports/digest_{ref_date.isoformat()}")
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    # ── JSON ──────────────────────────────────────────────────────────────
    json_path = Path(str(out_prefix) + ".json")
    israel_alerts = [a for a in alerts if a.get("israel_relevance_flag")]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at":  datetime.now().isoformat(),
                "window_days":   args.window,
                "window_start":  window_start.isoformat(),
                "ref_date":      ref_date.isoformat(),
                "n_in_window":   len(alerts),
                "n_critical":    n_critical,
                "n_high":        n_high,
                "n_medium":      n_medium,
                "n_israel":      n_israel,
                "alerts":        shown,
                "israel_alerts": israel_alerts,
            },
            f, indent=2, ensure_ascii=False,
        )
    print(f"Saved {json_path}")

    # ── HTML ──────────────────────────────────────────────────────────────
    sections_parts: list[str] = []
    tier_labels = {
        "critical": "🔴 קריטי",
        "high":     "🟠 גבוה",
        "medium":   "🟡 בינוני",
    }
    badge_map = {"critical": "c", "high": "h", "medium": "m"}

    # ── מקטע ישראל — מופיע ראשון, ללא קשר לציון ──────────────────────────
    if israel_alerts:
        sections_parts.append(
            f"<h2>🇮🇱 רלוונטי לישראל ({len(israel_alerts)})"
            f" <span style='font-size:13px;font-weight:normal;color:#555'>"
            f"— כל התראה שישראל הוזכרה בה, ללא קשר לציון</span></h2>"
        )
        for a in sorted(israel_alerts, key=lambda x: x["bi_encoder_score"], reverse=True):
            title  = (a.get("title") or a.get("product_description") or "ריקול")[:100]
            hazard = (a.get("hazard_specific") or a.get("hazard_category") or "לא צוין")[:60]
            tier_k = a.get("tier", "low")
            tier_he = a.get("tier_he", "נמוך")
            b = badge_map.get(tier_k, "m")
            # קבע את מקור הרלוונטיות
            dist_raw = a.get("distribution_countries") or ""
            origin   = a.get("origin_country") or ""
            if "israel" in origin.lower():
                israel_reason = f"מוצר מישראל ({origin})"
            elif "israel" in dist_raw.lower():
                israel_reason = "ישראל ברשימת מדינות ההפצה"
            else:
                israel_reason = "אזכור ישראל בטקסט"
            sections_parts.append(
                _CARD_IL.format(
                    title=title,
                    b=b,
                    tier_he=tier_he,
                    score=a["bi_encoder_score"],
                    pct=a["window_percentile"],
                    source_id=a["source_id"],
                    date_str=a.get("source_published_date") or "",
                    hazard=hazard,
                    severity_raw=a.get("severity_raw") or "",
                    israel_reason=israel_reason,
                    distribution=_dist_text(a.get("distribution_countries")),
                )
            )
        sections_parts.append("<hr>")

    for tier_key in ("critical", "high", "medium"):
        tier_alerts = [a for a in shown if a["tier"] == tier_key]
        if not tier_alerts:
            continue
        sections_parts.append(f"<h2>{tier_labels[tier_key]} ({len(tier_alerts)})</h2>")
        for a in tier_alerts:
            title  = (a.get("title") or a.get("product_description") or "ריקול")[:100]
            hazard = (a.get("hazard_specific") or a.get("hazard_category") or "לא צוין")[:60]
            sections_parts.append(
                _CARD.format(
                    cls=tier_key,
                    b=badge_map[tier_key],
                    title=title,
                    tier_he=a["tier_he"],
                    score=a["bi_encoder_score"],
                    pct=a["window_percentile"],
                    source_id=a["source_id"],
                    date_str=a.get("source_published_date") or "",
                    hazard=hazard,
                    severity_raw=a.get("severity_raw") or "",
                    distribution=_dist_text(a.get("distribution_countries")),
                )
            )

    html_path = Path(str(out_prefix) + ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(
            _HTML.format(
                date=ref_date.isoformat(),
                window_days=args.window,
                window_start=window_start.isoformat(),
                n_in_window=len(alerts),
                n_critical=n_critical,
                n_high=n_high,
                n_medium=n_medium,
                n_israel=n_israel,
                sections="\n".join(sections_parts),
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
        )
    print(f"Saved {html_path}")


if __name__ == "__main__":
    main()
