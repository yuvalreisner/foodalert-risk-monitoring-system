"""Export recalls (and optional BT scores) to Excel for sharing.

Usage:
  python3 scripts/export_recalls_excel.py --all
  python3 scripts/export_recalls_excel.py --sample labeling_v3 --with-bt
  python3 scripts/export_recalls_excel.py --all -o ~/Desktop/foodsafe_recalls.xlsx
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# openpyxl rejects XML 1.0 illegal control characters in cell text
_ILLEGAL_XLSX_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.report_links import source_label

DEFAULT_MODEL = "claude-sonnet-4-6"

ALERT_COLUMNS = """
    a.id,
    a.source_id,
    a.source_record_id,
    a.record_url,
    a.event_initiation_date,
    a.event_status,
    a.origin_country,
    a.distribution_countries,
    a.recalling_firm,
    a.brand_names,
    a.product_description,
    a.product_category,
    a.hazard_category,
    a.hazard_specific,
    a.severity_raw,
    a.severity_normalized,
    a.reason_for_recall,
    a.description,
    a.title
"""


def sanitize_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].map(
            lambda v: _ILLEGAL_XLSX_CHARS.sub("", v) if isinstance(v, str) else v
        )
    return out


def load_alerts(conn, sample: str | None) -> pd.DataFrame:
    if sample:
        sql = f"""
            SELECT {ALERT_COLUMNS}, sm.stratum
            FROM alerts a
            JOIN sample_members sm ON sm.alert_id = a.id AND sm.sample_name = ?
            ORDER BY a.source_id, a.event_initiation_date DESC
        """
        df = pd.read_sql_query(sql, conn, params=(sample,))
    else:
        sql = f"""
            SELECT {ALERT_COLUMNS}
            FROM alerts a
            ORDER BY a.source_id, a.event_initiation_date DESC
        """
        df = pd.read_sql_query(sql, conn)
    df.insert(1, "source_label", df["source_id"].map(source_label))
    return df


def load_bt_wide(conn, sample: str, model: str) -> pd.DataFrame:
    sql = """
        SELECT alert_id, dimension, score
        FROM bt_scores
        WHERE sample_name = ? AND label_model = ?
    """
    long = pd.read_sql_query(sql, conn, params=(sample, model))
    if long.empty:
        return long
    wide = long.pivot(index="alert_id", columns="dimension", values="score").reset_index()
    wide.columns.name = None
    return wide


def readme_rows(scope: str, n_alerts: int, n_bt: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Field": [
                "Project",
                "Export scope",
                "Rows (Recalls sheet)",
                "Rows with BT scores",
                "BT model",
                "Score interpretation",
                "Composite",
                "Sources",
            ],
            "Value": [
                "FoodSafe Intelligence (MBA capstone)",
                scope,
                str(n_alerts),
                str(n_bt),
                DEFAULT_MODEL,
                "Higher BT score = relatively more severe within LLM pairwise comparisons. "
                "Scores are mean-centered; use rank order only.",
                "Equal average of severity, likelihood, exposure (1/3 each).",
                "FDA openFDA, USDA FSIS, FSA UK",
            ],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export recalls to Excel (.xlsx)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="All recalls in alerts.db (~18k)")
    group.add_argument("--sample", metavar="NAME", help="Only recalls in a sample (e.g. labeling_v3)")
    parser.add_argument(
        "--with-bt",
        action="store_true",
        help="Add BT score columns (requires --sample; joins scores for that sample)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="BT label model")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .xlsx path (default: data/exports/<auto-name>.xlsx)",
    )
    args = parser.parse_args()

    if args.with_bt and not args.sample:
        parser.error("--with-bt requires --sample")

    conn = db.connect()
    sample = args.sample if args.sample else None
    df = load_alerts(conn, sample)

    bt = None
    if args.with_bt and sample:
        bt = load_bt_wide(conn, sample, args.model)
        df = df.merge(bt, left_on="id", right_on="alert_id", how="left")
        if "alert_id" in df.columns:
            df = df.drop(columns=["alert_id"])

    conn.close()

    if args.all:
        scope = "All recalls in database"
        default_name = "foodsafe_all_recalls.xlsx"
    elif args.with_bt:
        scope = f"Sample '{sample}' with Bradley-Terry scores"
        default_name = f"foodsafe_{sample}_with_bt.xlsx"
    else:
        scope = f"Sample '{sample}' (no BT scores)"
        default_name = f"foodsafe_{sample}_recalls.xlsx"

    out = Path(args.output) if args.output else Path("data/exports") / default_name
    out.parent.mkdir(parents=True, exist_ok=True)

    n_bt = 0
    if bt is not None and not bt.empty and "composite" in df.columns:
        n_bt = int(df["composite"].notna().sum())

    df = sanitize_for_excel(df)

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        readme_rows(scope, len(df), n_bt).to_excel(writer, sheet_name="README", index=False)
        df.to_excel(writer, sheet_name="Recalls", index=False)

    print(f"Wrote {out}")
    print(f"  Rows: {len(df):,}")
    if args.with_bt:
        print(f"  With composite BT score: {n_bt:,}")


if __name__ == "__main__":
    main()
