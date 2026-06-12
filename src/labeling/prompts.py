"""LLM prompt templates for pairwise food safety risk comparison.

Design principles applied:
  - Persona: anchor model in food safety expertise.
  - Definitions: each dimension is anchored to FDA's regulatory framework (21 CFR 7.41).
  - MOH calibration: expert pilot feedback (Ministry of Health, Israel) embedded in SYSTEM_PROMPT.
  - Chain-of-thought: brief reasoning before final answer improves calibration.
  - Structured output: JSON for parseability.
  - Order bias mitigation: handled outside the prompt — each pair is run twice with
    A and B swapped, and consistency is checked.
"""
from __future__ import annotations
import json


SYSTEM_PROMPT = """You are an expert in food safety, regulatory risk assessment, and \
public health policy. You advise the Israeli Ministry of Health (MOH) Food Risk \
Management Unit. You have deep familiarity with FDA, USDA, EU (FSA UK, RASFF-style \
alerts), and 21 CFR 7.41 — FDA's hazard evaluation criteria.

Your job is to compare two food safety recall alerts and decide which one poses a \
greater risk along three distinct dimensions. Rank for relevance to public-health \
decision-making in Israel, not only for the country listed in the recall text.

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

For each dimension, compare Alert A and Alert B and decide which poses GREATER risk \
in that dimension only.

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
  when relevant), then a decisive answer "A" or "B" — no equivocation.
"""


PAIR_USER_TEMPLATE = """Compare the following two food safety recall alerts.

=== ALERT A ===
{alert_a_text}

=== ALERT B ===
{alert_b_text}

For each of the three dimensions, provide brief reasoning (1-2 sentences) and then \
your final answer "A" or "B".

Respond ONLY in this JSON format, with no additional text before or after:

{{
  "severity": {{
    "reasoning": "...",
    "winner": "A"
  }},
  "likelihood": {{
    "reasoning": "...",
    "winner": "A"
  }},
  "exposure": {{
    "reasoning": "...",
    "winner": "A"
  }}
}}
"""


def render_alert_as_text(alert: dict) -> str:
    """Render a single alert as the natural-language template that the LLM and
    eventually the Bi-Encoder will consume.

    All structured fields are flattened into one prose paragraph so BERT can
    leverage its natural-language pretraining (rather than treating XML tags
    as opaque tokens).
    """
    firm = alert.get("recalling_firm") or "unknown firm"
    country = alert.get("origin_country") or "unknown country"
    product = alert.get("product_description") or "unspecified product"
    category = alert.get("product_category") or "uncategorized"
    hazard = alert.get("hazard_specific") or alert.get("hazard_category") or "unspecified hazard"
    hazard_cat = alert.get("hazard_category") or "unspecified type"
    severity_raw = alert.get("severity_raw") or "unclassified"
    distribution = alert.get("distribution_countries") or "[]"
    try:
        dist_list = json.loads(distribution) if isinstance(distribution, str) else distribution
    except json.JSONDecodeError:
        dist_list = [distribution]
    dist_text = ", ".join(dist_list) if dist_list else "not specified"
    description = (alert.get("description") or alert.get("reason_for_recall") or "").strip()

    return (
        f"Recall issued by {firm} from {country} for {product} "
        f"(category: {category}). "
        f"Hazard: {hazard} ({hazard_cat}). "
        f"Regulatory severity: {severity_raw}. "
        f"Distribution: {dist_text}. "
        f"Description: {description}"
    )


def build_user_prompt(alert_a: dict, alert_b: dict) -> str:
    return PAIR_USER_TEMPLATE.format(
        alert_a_text=render_alert_as_text(alert_a),
        alert_b_text=render_alert_as_text(alert_b),
    )
