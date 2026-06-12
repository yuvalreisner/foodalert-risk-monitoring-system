"""Step 8 — Counterfactual explainability analysis.

For each top-N (and bottom-N) alert, perturb one field at a time and
measure how the Bi-Encoder score changes. This answers: *why* did an alert
rank high or low? Which fields drive the score?

Perturbations run (one at a time, all others unchanged):
  hazard→Listeria      replace hazard with Listeria monocytogenes
  hazard→mineral_oil   replace with chronic chemical (MOSH/MOAH)
  hazard→allergen      replace with undeclared allergen
  severity→ClassI      set severity_raw = "Class I"
  severity→ClassIII    set severity_raw = "Class III"
  dist→nationwide      set distribution = nationwide US
  dist→local_only      set distribution = single local area
  dist→+Israel         append Israel to distribution_countries
  rte→add_RTE          prepend "Ready-to-eat product." to description
  rte→cooked           prepend "Requires thorough cooking." to description

Usage:
  # Daily incremental run — adds only new Critical/High alerts (default):
  python3 scripts/counterfactuals.py --tier critical,high --window 90

  # First-time bulk run (same as above, just takes longer):
  python3 scripts/counterfactuals.py --tier critical,high --window 90

  # Legacy: top-N + bottom-N by global score
  python3 scripts/counterfactuals.py --n 10
  python3 scripts/counterfactuals.py --alert-id <id>
  python3 scripts/counterfactuals.py --out reports/cf.json
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import torch
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db
from src.labeling.prompts import render_alert_as_text
from src.models.bi_encoder import BiEncoderRiskModel

DEFAULT_CHECKPOINT = Path("models/bi_encoder_labeling_v3/best_model.pt")

# Each perturbation: (name_en, name_he, field_or_action, value_or_None)
PERTURBATIONS: list[tuple[str, str, str, str | None]] = [
    ("hazard→Listeria",    "סיכון→ליסטריה",       "hazard_specific", "Listeria monocytogenes"),
    ("hazard→mineral_oil", "סיכון→שמן מינרלי",    "hazard_specific", "mineral oil MOSH/MOAH (chronic chemical)"),
    ("hazard→allergen",    "סיכון→אלרגן",          "hazard_specific", "undeclared allergen: peanuts, sesame"),
    ("severity→ClassI",    "חומרה→Class I",         "severity_raw",    "Class I"),
    ("severity→ClassIII",  "חומרה→Class III",       "severity_raw",    "Class III"),
    ("dist→nationwide",    "הפצה→ארצית",            "distribution_countries", '["United States"]'),
    ("dist→local_only",    "הפצה→מקומית",           "distribution_countries", '["limited local area, single county"]'),
    ("dist→+Israel",       "הפצה→+ישראל",           "_append_israel",  None),
    ("rte→add_RTE",        "מוצר→RTE",              "_prepend_desc",   "Ready-to-eat product. "),
    ("rte→cooked",         "מוצר→בישול נדרש",       "_prepend_desc",   "Requires thorough cooking before consumption. "),
]


def _apply(alert: dict, pert: tuple) -> dict:
    name_en, name_he, field, value = pert
    a = deepcopy(alert)
    if field == "_append_israel":
        try:
            countries = json.loads(a.get("distribution_countries") or "[]")
        except Exception:
            countries = []
        if "Israel" not in countries:
            countries.append("Israel")
        a["distribution_countries"] = json.dumps(countries)
    elif field == "_prepend_desc":
        orig = a.get("description") or a.get("reason_for_recall") or ""
        a["description"] = value + orig
    else:
        a[field] = value
    return a


@torch.no_grad()
def _score(model, tokenizer, device, max_length, alert: dict) -> float:
    text = render_alert_as_text(alert)
    enc = tokenizer(
        [text], truncation=True, max_length=max_length,
        padding=True, return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    return model.encode_text(enc["input_ids"], enc["attention_mask"]).item()


CRITICAL_THRESHOLD = 0.95
HIGH_THRESHOLD     = 0.80
MEDIUM_THRESHOLD   = 0.50

TIER_CUTOFFS = {
    "critical": CRITICAL_THRESHOLD,
    "high":     HIGH_THRESHOLD,
    "medium":   MEDIUM_THRESHOLD,
}


def _window_percentile(score: float, all_scores: list[float]) -> float:
    """Fraction of window alerts with score <= this score."""
    if not all_scores:
        return 0.0
    return sum(1 for s in all_scores if s <= score) / len(all_scores)


def _analyse_alert(alert: dict, model, tokenizer, device, max_length) -> dict:
    original_score = float(alert["bi_encoder_score"])
    original_pct   = alert.get("bi_encoder_percentile")
    title = (alert.get("title") or alert.get("product_description") or alert["id"])[:80]

    print(f"\n{'='*72}")
    print(f"  {title}")
    pct_str = f"  pct={original_pct:.2%}" if isinstance(original_pct, float) else ""
    print(f"  id={alert['id']}  score={original_score:+.4f}{pct_str}")
    print(f"  hazard={alert.get('hazard_specific') or '—'}"
          f"  sev={alert.get('severity_raw') or '—'}")
    print(f"  {'perturbation':35s}  {'delta':>8s}  {'before':>9s} → {'after':>9s}")
    print(f"  {'-'*35}  {'-'*8}  {'-'*9}   {'-'*9}")

    perts = []
    for pert in PERTURBATIONS:
        name_en = pert[0]
        perturbed = _apply(alert, pert)
        new_score = _score(model, tokenizer, device, max_length, perturbed)
        delta = new_score - original_score
        arrow = "↑" if delta > 0.005 else ("↓" if delta < -0.005 else "→")
        print(f"  {arrow} {name_en:33s}  {delta:+8.4f}  {original_score:+9.4f} → {new_score:+9.4f}")
        perts.append({
            "perturbation":    name_en,
            "perturbation_he": pert[1],
            "field":           pert[2],
            "new_value":       pert[3],
            "original_score":  round(original_score, 5),
            "perturbed_score": round(new_score, 5),
            "delta":           round(delta, 5),
            "direction":       arrow,
        })

    top_driver = max(perts, key=lambda p: abs(p["delta"]))
    print(f"\n  → Largest driver: {top_driver['perturbation']}  Δ={top_driver['delta']:+.4f}")

    return {
        "alert_id":            alert["id"],
        "title":               title,
        "source_id":           alert["source_id"],
        "hazard_specific":     alert.get("hazard_specific") or "",
        "severity_raw":        alert.get("severity_raw") or "",
        "original_score":      round(original_score, 5),
        "original_percentile": round(original_pct, 4) if isinstance(original_pct, float) else None,
        "top_driver":          top_driver["perturbation"],
        "perturbations":       perts,
    }


def _load_model(checkpoint: Path):
    ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
    backbone   = ckpt["backbone"]
    max_length = ckpt["max_length"]
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")
    tokenizer = AutoTokenizer.from_pretrained(backbone)
    model = BiEncoderRiskModel(backbone=backbone)
    model.load_state_dict(ckpt["model_state"])
    model.to(device).eval()
    return model, tokenizer, device, max_length


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    ap.add_argument("--out", type=Path, default=Path("reports/counterfactuals.json"))
    # Tier-based mode (daily pipeline)
    ap.add_argument("--tier", default=None,
                    help="Comma-separated tiers to process, e.g. critical,high")
    ap.add_argument("--window", type=int, default=90,
                    help="Days back from today for window-based tier calculation")
    ap.add_argument("--date", default=None, help="Reference date YYYY-MM-DD (default: today)")
    # Legacy mode
    ap.add_argument("--n", type=int, default=5, help="(Legacy) Top-N alerts to analyse")
    ap.add_argument("--also-bottom", type=int, default=2, help="(Legacy) Also analyse bottom-N")
    ap.add_argument("--alert-id", default=None, help="(Legacy) Analyse a single alert by id")
    args = ap.parse_args()

    model, tokenizer, device, max_length = _load_model(args.checkpoint)
    conn = db.connect()

    # ── Build alert list ──────────────────────────────────────────────────────
    if args.tier:
        # Tier-based: fetch all alerts in the window, compute window percentile,
        # keep only the requested tiers
        ref_date     = date.fromisoformat(args.date) if args.date else date.today()
        window_start = ref_date - timedelta(days=args.window)
        print(f"Window {window_start} – {ref_date}  (--window {args.window})")

        all_rows = conn.execute(
            "SELECT a.*, s.bi_encoder_score, s.bi_encoder_percentile "
            "FROM alerts a JOIN alert_scores s ON s.alert_id = a.id "
            "WHERE a.source_published_date BETWEEN ? AND ? "
            "ORDER BY s.bi_encoder_score DESC",
            (str(window_start), str(ref_date)),
        ).fetchall()

        if not all_rows:
            print("No scored alerts in window — run score_all_alerts.py first.")
            sys.exit(1)

        all_scores = [float(r["bi_encoder_score"]) for r in all_rows]
        requested_tiers = {t.strip().lower() for t in args.tier.split(",")}
        min_cutoff = min(TIER_CUTOFFS[t] for t in requested_tiers if t in TIER_CUTOFFS)

        rows = []
        for r in all_rows:
            wp = _window_percentile(float(r["bi_encoder_score"]), all_scores)
            if wp >= min_cutoff:
                d = dict(r)
                d["_window_percentile"] = wp
                rows.append(d)

        print(f"Tiers {args.tier}: {len(rows)} alerts in window")

    elif args.alert_id:
        rows = [dict(r) for r in conn.execute(
            "SELECT a.*, s.bi_encoder_score, s.bi_encoder_percentile "
            "FROM alerts a JOIN alert_scores s ON s.alert_id = a.id "
            "WHERE a.id = ?",
            (args.alert_id,),
        ).fetchall()]

    else:
        top = conn.execute(
            "SELECT a.*, s.bi_encoder_score, s.bi_encoder_percentile "
            "FROM alerts a JOIN alert_scores s ON s.alert_id = a.id "
            "ORDER BY s.bi_encoder_score DESC LIMIT ?",
            (args.n,),
        ).fetchall()
        bottom = conn.execute(
            "SELECT a.*, s.bi_encoder_score, s.bi_encoder_percentile "
            "FROM alerts a JOIN alert_scores s ON s.alert_id = a.id "
            "ORDER BY s.bi_encoder_score ASC LIMIT ?",
            (args.also_bottom,),
        ).fetchall()
        rows = [dict(r) for r in list(top) + list(bottom)]

    conn.close()

    if not rows:
        print("No alerts to analyse.")
        sys.exit(1)

    # ── Load existing results and skip already-computed alerts ────────────────
    existing: dict[str, dict] = {}
    if args.out.exists():
        try:
            with open(args.out, encoding="utf-8") as f:
                saved = json.load(f)
            for entry in saved.get("analyses", []):
                existing[entry["alert_id"]] = entry
            print(f"Loaded {len(existing)} existing analyses from {args.out}")
        except Exception as e:
            print(f"Warning: could not load existing file ({e}) — starting fresh")

    to_run = [r for r in rows if r["id"] not in existing]
    skipped = len(rows) - len(to_run)
    if skipped:
        print(f"Skipping {skipped} already-computed alerts  →  {len(to_run)} new to process")
    if not to_run:
        print("All alerts already computed — nothing to do.")
        return

    # ── Run counterfactuals ───────────────────────────────────────────────────
    new_analyses = []
    for i, alert in enumerate(to_run, 1):
        print(f"\n[{i}/{len(to_run)}]", end="")
        new_analyses.append(_analyse_alert(alert, model, tokenizer, device, max_length))

    # ── Merge and save ────────────────────────────────────────────────────────
    merged: dict[str, dict] = {**existing}
    for a in new_analyses:
        merged[a["alert_id"]] = a

    # Preserve insertion order: existing first, new appended
    all_analyses = list(existing.values()) + new_analyses

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"n_alerts": len(all_analyses), "analyses": all_analyses},
                  f, indent=2, ensure_ascii=False)
    print(f"\nSaved {args.out}  ({len(all_analyses)} total, {len(new_analyses)} new)")


if __name__ == "__main__":
    main()
