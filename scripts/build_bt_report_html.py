"""Embed bt_report_data.json into reports/bt_scores_ranking.html."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "bt_report_data.json"
TEMPLATE_PATH = ROOT / "reports" / "bt_scores_ranking.template.html"
OUT_PATH = ROOT / "reports" / "bt_scores_ranking.html"


def main() -> None:
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH} — run scripts/export_bt_report.py first", file=sys.stderr)
        sys.exit(1)
    if not TEMPLATE_PATH.exists():
        print(f"Missing {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False)
    html = template.replace("/*__BT_DATA__*/", payload)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
