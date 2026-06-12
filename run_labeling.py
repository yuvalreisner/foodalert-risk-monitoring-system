"""
Food-safety recall pair labeling script.
Calls Claude claude-sonnet-4-6 in batches of 15 pairs.
Saves results incrementally to data/llm_labels_v3.json.
"""

import json
import os
import time
import sys
from pathlib import Path

import anthropic

# ── paths ────────────────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).resolve().parent / "data"
INPUT_FILE = DATA_DIR / "labeling_pairs_v3_for_llm.json"
OUTPUT_FILE = DATA_DIR / "llm_labels_v3.json"
BATCH_SIZE = 15

# ── prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert in food safety, regulatory risk assessment, and public health policy. You advise the Israeli Ministry of Health (MOH) Food Risk Management Unit. You have deep familiarity with FDA, USDA, EU (FSA UK, RASFF-style alerts), and 21 CFR 7.41 — FDA's hazard evaluation criteria.

Your job is to compare two food safety recall alerts and decide which one poses a greater risk along three distinct dimensions. Rank for relevance to public-health decision-making in Israel, not only for the country listed in the recall text.

1. SEVERITY — How harmful would the contamination be to a person who is actually
   exposed? Consider mortality risk, severity of illness, hospitalization likelihood,
   long-term health consequences, and reversibility. This corresponds to 21 CFR 7.41(d).
   Examples of high severity: Listeria in ready-to-eat foods (high mortality in
   vulnerable populations), botulinum toxin, undeclared allergens that cause
   anaphylaxis.
   Examples of lower severity for a single exposure event: chronic chemical hazards
   (PFAS, PFOA/PFOS, MOAH/MOSH) where harm requires prolonged intake; cosmetic
   mislabeling; minor under-fill quantity.

2. LIKELIHOOD — How likely is harm to actually occur given the contamination level,
   product use, and distribution? Consider: typical preparation (cooked vs. eaten raw),
   contamination dose, time to consumption, consumer awareness. This corresponds to
   21 CFR 7.41(e).
   Examples of high likelihood: ready-to-eat (RTE) product with confirmed hazard
   (e.g. environmental Listeria on a slicer used for RTE sandwiches); undeclared
   allergen in a product allergic consumers will eat.
   Examples of low likelihood: hazard reduced by thorough cooking/heating before
   consumption; chronic contaminants where a single serving is unlikely to cause
   measurable acute harm; physical foreign material that may remain inside packaging.

3. EXPOSURE — How many people are likely to be affected? Consider: distribution
   volume, geographic spread (single store vs. nationwide vs. multi-country),
   consumer reach, product popularity, vulnerable populations. This corresponds to
   21 CFR 7.41(c) and (f).
   Do not treat the distribution field naively: a country named may be origin,
   primary market, or one leg of trade — consider whether the product plausibly
   reaches larger populations or import routes (including indirect relevance to Israel
   via EU/UK/US supply chains).
   Examples of high exposure: nationwide or country-wide retail distribution;
   products popular with children; large-volume staples.
   Examples of low exposure: limited corporate sites, small recalled quantity before
   wide retail spread, professional/B2B-only channels with few end consumers.

For each dimension, compare Alert A and Alert B and decide which poses GREATER risk in that dimension only.

MOH expert calibration (apply in every comparison):
- Acute vs chronic: This is the main lens. Undeclared allergens can cause severe or
  fatal reactions from a single exposure — even a small amount — and should usually
  rank high on SEVERITY and LIKELIHOOD versus chronic chemical risks (PFAS, mineral
  oils MOAH/MOSH) that need sustained consumption over time. Do not treat long-term
  carcinogenic potential as higher severity than acute anaphylaxis risk for a typical
  one-time consumption scenario.
- Ready-to-eat vs cook-before-eating: If consumers eat the product without a cooking
  step that reliably reduces the hazard, treat severity and likelihood more seriously
  than for raw meat or items normally cooked/heated before eating (unless contamination
  is confirmed in the final RTE product).
- Vulnerable populations: Children, pregnant and nursing women, elderly, allergic,
  and immunocompromised groups count heavily — a product popular with children can have
  high impact even when per-serving chemical dose looks low. Lower population exposure
  can still mean severe outcomes in these groups.
- Israel relevance: Favor alerts with plausible pathways to Israel — direct mention,
  major export markets, or distribution in countries that often re-export to Israel
  (e.g. UK/EU alerts on widely traded branded goods). This mainly affects EXPOSURE
  and can raise overall priority when trade relevance is plausible.
- Allergens: Classic high-priority acute hazard; wheat, milk, soy, fish, shellfish,
  sesame, etc. in RTE or mislabeled products.
- Physical hazards (plastic, rubber, metal): If fragment size, whether pieces stay in
  packaging, or consumer detection is unclear, note uncertainty; do not assume worst
  case without evidence. Bulk industrial ingredients (e.g. glaze sold to bakeries)
  can imply very wide downstream exposure even when the recall text is brief.
- Process-only violations (cGMP, documentation, missing nutrients) without confirmed
  contamination or allergen in the recalled lot: generally lower severity and
  likelihood than confirmed allergen or pathogen events.

General rules:
- Each dimension is independent. Alert A may win on SEVERITY but lose on EXPOSURE.
- If genuinely unsure after applying the rules above, prefer the alert with stronger
  regulatory classification (FDA Class I > Class II > Class III; FAFA > PRIN > AA).
- Brief reasoning required (state acute/chronic, RTE/cooking, or Israel/trade logic
  when relevant), then a decisive answer "A" or "B" — no equivocation."""


def make_user_prompt(pairs_batch):
    """Build a user prompt for a batch of pairs, asking for JSON array output."""
    lines = []
    lines.append(f"Label the following {len(pairs_batch)} food safety recall pairs.")
    lines.append("For each pair, provide reasoning (1-2 sentences each) and winner (A or B) for severity, likelihood, and exposure.")
    lines.append("")
    lines.append("Respond ONLY with a JSON array — one object per pair, in order. No text before or after.")
    lines.append("Schema per object:")
    lines.append("""{
  "pair_id": "...",
  "category": "...",
  "severity":   {"winner": "A", "reasoning": "..."},
  "likelihood": {"winner": "B", "reasoning": "..."},
  "exposure":   {"winner": "A", "reasoning": "..."}
}""")
    lines.append("")

    for p in pairs_batch:
        lines.append(f"=== PAIR pair_id={p['pair_id']} category={p['category']} ===")
        lines.append("--- ALERT A ---")
        lines.append(p["alert_a"]["text"])
        lines.append("--- ALERT B ---")
        lines.append(p["alert_b"]["text"])
        lines.append("")

    return "\n".join(lines)


def call_claude(client, pairs_batch, retries=3):
    prompt = make_user_prompt(pairs_batch)
    for attempt in range(1, retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown code block if present
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"  JSON parse error (attempt {attempt}): {e}")
            if attempt == retries:
                raise
            time.sleep(5)
        except Exception as e:
            print(f"  API error (attempt {attempt}): {e}")
            if attempt == retries:
                raise
            time.sleep(10)


def main():
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    with open(INPUT_FILE) as f:
        data = json.load(f)
    pairs = data["pairs"]
    print(f"Loaded {len(pairs)} pairs.")

    # Load existing results if any
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            results = json.load(f)
        done_ids = {r["pair_id"] for r in results}
        print(f"Resuming: {len(done_ids)} already labeled.")
    else:
        results = []
        done_ids = set()

    # Filter to unlabeled pairs
    remaining = [p for p in pairs if p["pair_id"] not in done_ids]
    print(f"Remaining: {len(remaining)} pairs to label.")

    total_labeled = len(done_ids)
    batch_num = 0

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i : i + BATCH_SIZE]
        batch_num += 1
        print(f"\nBatch {batch_num}: pairs {i+1}–{min(i+BATCH_SIZE, len(remaining))} of {len(remaining)} remaining...", flush=True)

        try:
            batch_results = call_claude(client, batch)
        except Exception as e:
            print(f"  FAILED batch {batch_num}: {e}")
            print("  Saving progress and stopping.")
            break

        # Validate and append
        for res in batch_results:
            if res.get("pair_id") and res["pair_id"] not in done_ids:
                results.append(res)
                done_ids.add(res["pair_id"])

        total_labeled = len(results)
        print(f"  ✓ Batch done. Total labeled so far: {total_labeled}", flush=True)

        # Save after every batch
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Small pause to be nice to the API
        time.sleep(1)

    print(f"\n=== Done. Total labeled: {len(results)} / {len(pairs)} ===")
    # Verify unique pair_ids
    unique_ids = {r["pair_id"] for r in results}
    print(f"Unique pair_ids: {len(unique_ids)}")
    if len(results) == 299:
        print("✓ All 299 pairs labeled successfully.")
    else:
        missing = [p["pair_id"] for p in pairs if p["pair_id"] not in unique_ids]
        print(f"Missing {len(missing)} pairs: {missing[:10]}")


if __name__ == "__main__":
    main()
