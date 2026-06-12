# Workspace Rules — mba_capstone

This is Yuval's capstone project for his MBA Big Data course at the Hebrew University of Jerusalem. This is academic work, NOT related to his job at Wix.

---

## Primary Source of Truth

**Always read [PROJECT.md](./PROJECT.md) first.** It is the central, continuously-updated project document containing: goals, methodology decisions, data sources, schema, current status, open questions, and next steps. This file (`CLAUDE.md`) contains only behavior rules for Claude — substantive project content lives in `PROJECT.md`.

When project decisions change (methodology, scope, sources, schema), update `PROJECT.md` and add an entry to its Changelog section.

---

## Project Overview

**Course**: פרוייקט סיום בביג דאטא (Capstone Project in Big Data) — course code **55910**
**Institution**: The Hebrew University of Jerusalem (האוניברסיטה העברית בירושלים) — School of Business Administration, Mount Scopus campus
**Credits**: 3, Master's level, taught in Hebrew
**Sponsor**: Israeli Ministry of Health (משרד הבריאות) — Health Regulation Division for Food, Alcoholic Beverages & Cosmetics — Food Risk Management Unit (היחידה לניהול סיכונים במזון)

**Goal**: Build an open-source intelligence (OSINT) tool for food safety **alerts only**, drawing **only from official sources** (UN, US, EU regulatory bodies and similar). There is **no explicit geographic filter** — the geographic coverage is whatever the chosen official sources naturally cover.

**Central business question (verbatim from the project brief):**

> כיצד ניתן לפתח מערכת מודיעין גלוי אוטומטית שתזהה במהירות ובדיוק איומי ביטחון מזון מתפתחים ותספק לקובעי המדיניות במשרד הבריאות מידע עדכני ומעובד לקבלת החלטות מהירות?

**Refined research question (decided in 29.03.2026 meeting):**

> כיצד ניתן להשתמש במודלי שפה גדולים (LLMs) כדי לאסוף, לאחד, לסווג ולדרג מידע ממקורות הטרוגניים (אתרי רגולציה, חדשות), לצורך זיהוי אוטומטי של התראות (Alerts) ומגמות (Trends) בתחום בטיחות המזון במדינות מפותחות?

### Output: Alerts Only

The tool produces a single type of output — **Alerts**: time-sensitive food safety events (recalls, outbreaks, enforcement actions). Trend analysis / consumption-pattern tracking is **out of scope** for this project.

Only deviations above a severity threshold qualify (definition of "big" vs. "small" is TBD).

### What Counts as Food Safety

Safe food: not spoiled, free of chemical contamination, and free of microbiological hazards (salmonella, listeria, microplastics, etc.).

### Source Types — Official Only

The tool ingests **only from official sources**: regulatory authorities of the UN, US, EU, and similar (e.g., FDA, USDA-FSIS, EFSA, WHO, INFOSAN, RASFF, USA Federal Register). Social media, hashtags, news aggregators, blogs, and informal sources are **out of scope**.

**Deduplication / record linkage is still required**, since the same event commonly surfaces across multiple official sources (e.g., an FDA recall mirrored by an INFOSAN notification and an EFSA alert).

### Expected Deliverables (4)

1. **Active OSINT system** — automatic ingestion, filtering, prioritization, classification, pattern/trend identification.
2. **Periodic reports & alerts** — daily/weekly/monthly digests pushed by email to stakeholders + immediate push notifications for critical events; archive of past updates.
3. **Comprehensive technical documentation + handover-ready system** — documented code, architecture diagrams, install/operate/maintain/extend guide, in cooperation with Ministry IT.
4. **Course deliverable** — per the syllabus: a written summary document + presentation in front of the company (Ministry of Health) and the class. Final grading: oral exam 40%, presentation 20%, written/other 30%, participation 10% (subject to change). Required attendance: 80%.

### Methodological Foundations

**Papers in `references/papers/`** — candidate methodologies to consider (none committed yet):
- **Risk-scoring** → `FAO_food_safety_risk_ranking.pdf` + `Kaplan_Garrick_1981_risk_definition.pdf` (the "set of triplets" definition of risk).
- **Interpretable alert prioritization** → `Rudin_2022_interpretable_scoring_systems.pdf`.
- **Text classification / extraction** → `UKHSA_2024_LLMs_for_public_health.pdf`.
- **Peripheral** → `HFES_2023_patient_safety_events_NLP.pdf` (general safety-event NLP technique, not food-specific).

**Required course reading** (from syllabus, course 55910):
- Powell, S.J. and Batt, R.J. (2011). *Modeling for Insight: A Master Class for Business Analysts*. John Wiley & Sons.
- Provost, F. and Fawcett, T. (2013). *Data Science for Business: What you need to know about data mining and data-analytic thinking*. O'Reilly Media.

These books are not in `references/` (they're textbooks); reference them by citation when they're directly relevant to a discussion.

### Methodology — Open

**No model architecture or methodology has been chosen yet.** The intent is to evaluate several candidate models against the actual data once collected, and pick what fits this type of project. Decision will be made in a future session.

Do **not** assume any specific approach (Bradley-Terry, Cross-Encoder, BERT, LLM-as-judge, etc.) is committed — these have all been mentioned in past discussions but none is binding. The papers in `references/papers/` are candidate methodologies to consider, not commitments.

The FDA's 3-tier alert severity classification is a useful **reference frame** for the eventual scoring scheme, regardless of which model architecture is chosen.

### Current Phase: Methodology Survey

The team is currently in a **literature-review / methodology-survey phase**. The active goal is:

> Gather a variety of methodologies and learn about scoring and risk-management models, in order to choose the model best suited to the project.

Inputs to this phase:
- The papers in `references/papers/`.
- Required course reading (Powell & Batt; Provost & Fawcett).
- Additional ideas surfaced by the lecturers in class (logged in `briefing/meeting_notes.md` when captured).
- Yuval may add new sources to `references/` over time.

The output of this phase is a **shortlist of candidate models** with pros/cons, leading to a model-selection decision. Implementation work (data collection, model training, system architecture) comes **after** this phase — do not jump ahead unless explicitly asked.

---

## Team

**Students** (working together on this project):
- Yuval Reisner (the user)
- Noy (נוי)
- Yuvali (יובלי)

**Academic lecturers** (course instructors at HUJI):
- Prof. Lev Muchnik (פרופ' לב מוצ'ניק) — lev.muchnik@mail.huji.ac.il, office hours Tue 14:00–15:00
- Prof. Nicole Adler (פרופ' ניקול אדלר)

**Domain advisors** (Israeli Ministry of Health):
- Dr. Matan Shiner (מתן שיינר) — matan.shiner@moh.gov.il, 054-4969304
- Dr. Noga Naor (נגה נאור) — noga.naor@moh.gov.il, 054-2442506

When generating content, communications, or shared deliverables, distinguish between the academic supervisors at HUJI (grading & methodology) and the domain advisors at the Ministry of Health (project content & sponsor).

---

## Data Sources

The initial source list lives in `briefing/initial_sources_list.xlsx`. Sources are organized into four categories with ratings (1–5) for freshness, accuracy, relevance, and coverage:

1. **Recalls and alerts** (9 sources): FDA recall enforcement reports, FDA import alerts, FDA safety alerts, FDA Recalls/Market Withdrawals/Safety Alerts, USDA-FSIS, RASFF window (EU), INFOSAN (global), CDC food safety aggregate.
2. **Outbreak investigations / morbidity** (4 sources): FDA CARES, FDA CORE outbreak investigations, CDC outbreaks, USDA outbreak investigations.
3. **Regulation and risk management** (4 sources): WHO news, EFSA, EFSA Journal, USA Federal Register.
4. **Trends and innovation in food production / consumption / industry** — placeholder, not yet populated. Students need to fill this in.

When asked about specific source ratings or details, read the xlsx for the full table.

---

## Working Language

- Project documents, communications with advisors, and the final report are likely in **Hebrew**.
- Code, technical comments, file names, and folder structure should remain in **English**.

---

## Folder Structure

| Folder | What it's for |
|--------|---------------|
| `briefing/` | Project briefing materials, course syllabus, and ongoing meeting record: `project_brief.docx`, `project_pitch_deck.pptx`, `initial_sources_list.xlsx`, `course_syllabus.pdf`, `meeting_notes.md`. **Read these for authoritative project specs, course requirements, and the latest direction.** |
| `references/papers/` | Academic papers establishing methodology (risk theory, scoring systems, NLP for public health). |

Additional folders (e.g., `data/`, `notebooks/`, `src/`, `report/`) will be added as the project develops — don't pre-create them.

---

## Behavior Rules

1. **Read `briefing/` first.** Before answering substantive questions about the project's scope, model design, or data sources, check what's in `briefing/`. The brief docx and pitch deck are the authoritative project specs.
2. **Don't conflate with the Wix work.** The team-wide `team/` memory and Wix-specific skills (Wixer, Trino, MBR, etc.) are not relevant here. If a Wix-specific tool seems applicable, double-check before using it.
3. **Academic integrity.** This is graded coursework. Do not generate full essay sections or final write-ups end-to-end without Yuval's input — assist with structure, analysis, code, and review, but the substantive intellectual contribution should be his and his teammates'.
4. **Confidentiality.** Material from the Ministry of Health may be sensitive. Don't push project content to public Gists, public repositories, or external services without explicit confirmation.
