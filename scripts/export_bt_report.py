"""Export Bradley-Terry ranking slices for the HTML report (with source links)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.bradley_terry import DIMENSIONS
from src.report_links import build_alert_links, source_label

TOP_N = 20
BOTTOM_N = 10


def enrich_row(conn, alert_id: str, score: float) -> dict:
    row = conn.execute(
        """
        SELECT id, source_id, source_record_id, record_url,
               severity_raw, severity_normalized,
               recalling_firm, product_description, reason_for_recall,
               event_initiation_date
        FROM alerts WHERE id = ?
        """,
        (alert_id,),
    ).fetchone()
    if not row:
        return {"id": alert_id, "score": score, "links": []}

    product = row[7]
    if product and len(product) > 160:
        product = product[:157] + "..."

    reason_for_recall = row[8] or None

    source_id = row[1]
    source_record_id = row[2]
    record_url = row[3]

    return {
        "score": score,
        "id": row[0],
        "source_id": source_id,
        "source_label": source_label(source_id),
        "source_record_id": source_record_id,
        "record_url": record_url,
        "links": build_alert_links(source_id, source_record_id, record_url),
        "event_date": row[9],
        "severity_raw": row[4],
        "severity_normalized": row[5],
        "recalling_firm": row[6],
        "product": product,
        "reason_for_recall": reason_for_recall,
    }


def export_dimension(conn, sample: str, model: str, dimension: str) -> dict:
    cur = conn.execute(
        """
        SELECT alert_id, score FROM bt_scores
        WHERE sample_name = ? AND dimension = ? AND label_model = ?
        ORDER BY score DESC
        """,
        (sample, dimension, model),
    )
    rows = [{"alert_id": r[0], "score": r[1]} for r in cur]
    top = [enrich_row(conn, r["alert_id"], r["score"]) for r in rows[:TOP_N]]
    bottom = [enrich_row(conn, r["alert_id"], r["score"]) for r in rows[-BOTTOM_N:]]
    bottom.reverse()
    return {"top": top, "bottom": bottom}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="labeling_v3")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument(
        "-o",
        "--output",
        default="data/bt_report_data.json",
        help="JSON path for report embed",
    )
    args = parser.parse_args()

    conn = db.connect()
    out: dict = {}
    for dim in list(DIMENSIONS) + ["composite"]:
        out[dim] = export_dimension(conn, args.sample, args.model, dim)
    conn.close()

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {path} ({len(out)} dimensions)")


if __name__ == "__main__":
    main()
