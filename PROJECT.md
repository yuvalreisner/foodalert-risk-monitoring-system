# FoodSafe Intelligence — מסמך פרויקט מרכזי

מסמך זה הוא המקור היחיד לאמת על הפרויקט. הוא מתעדכן באופן שוטף, ומיועד לשמש כקונטקסט עיקרי לשיחות עתידיות עם Claude וכבסיס למצגת הסופית בקורס.

עדכון אחרון: 2026-06-08 (RASFF collector נוסף)

---

## 1. זהות הפרויקט

פרויקט גמר MBA בקורס **פרוייקט סיום בביג דאטא** (קוד 55910), בית הספר למנהל עסקים, האוניברסיטה העברית בירושלים, הר הצופים. הקורס נלמד בעברית, 3 נקודות זכות, רמת מאסטר.

### ספונסר

משרד הבריאות — מערך רגולציה בריאות (מזון, משקאות משכרים ותמרוקים), היחידה לניהול סיכונים במזון.

### צוות הסטודנטים

- יובל רייזנר
- נוי
- יובלי

### מנחים אקדמיים (אוניברסיטה עברית)

- פרופ' לב מוצ'ניק (lev.muchnik@mail.huji.ac.il, שעות קבלה: שלישי 14:00–15:00)
- פרופ' ניקול אדלר

### יועצי תוכן (משרד הבריאות)

- ד"ר מתן שיינר (matan.shiner@moh.gov.il, 054-4969304)
- ד"ר נגה נאור (noga.naor@moh.gov.il, 054-2442506)

---

## 2. רקע ומוטיבציה

מערך רגולציה בריאות במשרד הבריאות אחראי על הבטחת בטיחות המזון בישראל כחלק מהגנה על בריאות הציבור. האיומים על בטיחות המזון מגוונים — זיהומים מיקרוביולוגיים (ליסטריה, סלמונלה, אי-קולי), מזהמים כימיים, מתכות כבדות, אלרגנים, מיקרו-פלסטיקים, שאריות חומרי הדברה ועוד. האיומים מתממשים לאורך כל שרשרת האספקה — ייצור, חקלאות, יבוא, שינוע, שיווק.

השוק העולמי הוא הזדמנות (גיוון סל המזונות, מחירים אטרקטיביים) וסיכון (מקורות מגוונים מגדילים את מגוון האיומים). הזמינות הגוברת של מידע ציבורי באינטרנט — אתרי רגולציה, פיידים, APIs — יוצרת הזדמנות לפתח מערכת מודיעין גלוי שתאפשר זיהוי מוקדם של איומים ומגמות, ותאפשר לרגולטור הישראלי להיערך מבעוד מועד.

---

## 3. שאלת המחקר

### השאלה העסקית המרכזית (מהבריף הרשמי)

> כיצד ניתן לפתח מערכת מודיעין גלוי אוטומטית שתזהה במהירות ובדיוק איומי ביטחון מזון מתפתחים ותספק לקובעי המדיניות במשרד הבריאות מידע עדכני ומעובד לקבלת החלטות מהירות?

### שאלת המחקר המעודכנת (פגישה 29.03.2026)

> כיצד ניתן להשתמש במודלי שפה גדולים (LLMs) כדי לאסוף, לאחד, לסווג ולדרג מידע ממקורות הטרוגניים (אתרי רגולציה, חדשות), לצורך זיהוי אוטומטי של התראות (Alerts) ומגמות (Trends) בתחום בטיחות המזון במדינות מפותחות?

### שאלת המחקר המעודכנת שוב (פגישה 11.05.2026)

המרצים העירו שהשאלה הקודמת מתמקדת מדי בטכנולוגיה (LLMs) ולא בבעיה. הניסוח המתוקן:

> כיצד ניתן לבנות מערכת אוטומטית שתדרג התראות בטיחות מזון לפי רלוונטיות וחומרה למשרד הבריאות בישראל, ותציף רק את אלה הדורשות התייחסות מיידית?

ה-LLMs נכנסים כמתודולוגיה אפשרית, לא כמהות.

---

## 4. היקף הפרויקט

### בתוך ההיקף

- פלט מסוג Alerts בלבד — אירועים רגישים לזמן (ריקולים, התפרצויות, פעולות אכיפה).
- מקורות רשמיים בלבד — רשויות רגולציה של ארה"ב, אירופה, האו"ם וכדומה.
- כיסוי גיאוגרפי הנגזר מבחירת המקורות הרשמיים, ללא פילטר גיאוגרפי מפורש.
- ניטור התראות הקשורות במישרין או בעקיפין לישראל (שדה `israel_relevance_flag` בסכמה).
- מערכת deduplication ו-record linkage בין מקורות.

### מחוץ להיקף

- ניתוח מגמות צריכה (Trends) — הוצא מההיקף בהחלטה מאוחרת.
- רשתות חברתיות, האשטאגים, גוגל טרנדס — לא מקורות רשמיים.
- אתרי חדשות לא רגולטוריים, בלוגים, אגרגטורים בלתי רשמיים.

### הגדרת בטיחות מזון

מזון בטוח: לא מקולקל, ללא זיהום כימי, ללא פתוגנים מיקרוביולוגיים (סלמונלה, ליסטריה, מיקרו-פלסטיקים).

---

## 5. מתודולוגיה — תוכנית עבודה ב-8 שלבים

המתודולוגיה עודכנה לאחר פגישת המרצים ב-11.05.2026. השינויים העיקריים: הגדלת המדגם ל-500, שילוב ממדים בממוצע שווה (לא Bootstrap), החלפת Cross-Encoder ב-Bi-Encoder עם BCE על הפרש ציונים.

### שלב 0 — איסוף הדאטה הגולמי

3 מקורות API: FDA Enforcement, USDA FSIS, FSA UK. נוסף — להעמיק לחלון של 3 שנים ולהסיר limit להגדיל את המאגר ל-10,000+ רשומות (החלטה מ-11.05).

### שלב 1 — דגימה סטרטיפית של 500 ריקולים

שכבות לפי severity_normalized (high/medium/low), עם בלאנס משני לפי source ו-hazard_category. **שינוי מ-100 ל-500**: סיכון overfitting קטן יותר, יותר דאטה לאימון Bi-Encoder.

### שלב 2 — תיוג ראשוני עם LLM

ה-LLM (Claude Sonnet 4.6) משווה זוגות. שלוש שאלות לכל זוג, אחת לכל ממד:
- severity — 21 CFR 7.41(d)
- likelihood — 21 CFR 7.41(e)
- exposure — 21 CFR 7.41(c) + (f)

בחירת זוגות: 299 זוגות אסטרטגיים מ-500 הדגימה, מקובצים ל-8 קטגוריות:
- same-severity (33 לכל אחד מ-3 דרגות) = 99
- adjacent (high-medium, medium-low) = 100
- polar (high-low) = 50
- cross-source (FDA vs FSA UK) = 50

אימות אנושי (סופי): **תיוג מומחים מלא לא יתבצע.** במקום זאת נערך **שאלון אימות איכותני על 5 זוגות** — הצוות תייג 5 זוגות מייצגים (severity/likelihood/exposure) והשווה את שיקול הדעת שלו לתיוג ה-LLM. התוצאות והנימוקים (בעברית) ב-`expert_review_2026-05-18.json`, הטופס ב-`expert_review.html`. מסקנה: הסכמה גבוהה עם ה-LLM, והפערים נבעו בעיקר מהבחנת acute מול chronic ומ-RTE מול מבושל — בדיוק העקרונות שכבר עוגנו ב-system prompt. השאלון משמש כ-sanity check לאיכות התיוג, לא כטבלת תוויות לאימון (טבלת `expert_labels` נשארת ריקה במכוון).

### שלב 3 — Bradley-Terry על שלושה ממדים

שלוש ריצות נפרדות:
```
BT_severity   = fit(טבלת תוויות severity)   →  500 ציוני severity
BT_likelihood = fit(טבלת תוויות likelihood) →  500 ציוני likelihood
BT_exposure   = fit(טבלת תוויות exposure)   →  500 ציוני exposure
```

Bradley-Terry לא משווה — הוא רק לוקח את התוצאות של ה-LLM ומחלץ ציונים מספריים באמצעות Maximum Likelihood Estimation.

### שלב 4 — שילוב ממדים: ממוצע שווה (Composite)

**החלטה מעודכנת (לאחר דיון עם המרצים):** במקום Bootstrap + Inverse Variance Weighting, משתמשים בממוצע פשוט ושווה של שלושת ציוני ה-BT:

```
composite = (BT_severity + BT_likelihood + BT_exposure) / 3
```

- משקל ⅓ לכל ממד — פשוט, שקוף, קל להסבר למשרד הבריאות.
- בעתיד ניתן לתת משקל גבוה יותר ל-severity (לפי העדפת MOH) — לא חלק מה-MVP.
- **סטטוס (2026-05-21):** מיושם ב-`bt_scores` (dimension=`composite`), 330 ריקולים עם ציון מלא (170 מ-500 ללא ציון — לא הופיעו באף זוג LLM).

> הערה: Bootstrap+IVW נדון בשיעור 11.05 אך לא יושם; נשאר כאפשרות post-MVP אם תידרש הערכת אי-ודאות פורמלית.

### שלב 5 — הרחבת דאטת האימון (זוגות סינתטיים)

מכל ריקולים שיש להם `composite` BT score, מייצרים **כל** זוגות האפשריים (או תת-קבוצה מסוננת).

דוגמה: 330 ריקולים עם ציון → C(330,2) ≈ 54,285 זוגות; 500 עם ציון מלא → 124,750.

**תווית לכל זוג (A, B):**
```
if composite_A > composite_B  →  winner = A  (label = 1 למודל)
if composite_A < composite_B  →  winner = B  (label = 0)
if composite_A == composite_B →  דילוג או תווית tie (נדיר)
```

אין קריאות LLM נוספות — התוויות נגזרות ישירות מציוני ה-BT.  
**חשוב:** train/test split ברמת **alert** (לא ברמת זוג), כדי למנוע דליפה.

### שלב 6 — אימון Bi-Encoder (Siamese) + BCE על הפרש ציונים

**תיקון מהשיעור ב-11.05.** ארכיטקטורה: Bi-Encoder (לא Cross-Encoder) — כל ריקול מקודד פעם אחת ב-inference.

```
Alert A text → Natural Template → BERT → embedding → linear head → score_A
                                           ↑↑ same weights ↓↓
Alert B text → Natural Template → BERT → embedding → linear head → score_B

Δ_pred = score_A - score_B
y      = 1  if composite_A > composite_B  else 0

Loss = BCE( σ(Δ_pred), y )    # Binary Cross-Entropy on score difference
```

- **Backbone:** RoBERTa או ModernBERT (pre-trained).
- **Loss:** BCE על σ(score_A − score_B) מול תווית "מי composite גבוה יותר" — לא Margin Loss.
- יתרון: המודל לומד סדר יחסי שמתאים ל-BT; בייצור מחשבים `score` לכל ריקול בנפרד.

ייצוג קלט (Natural Template, לא XML):
```
Recall issued by [recalling_firm] from [origin_country] for [product_description]
(category: [product_category]). Hazard: [hazard_specific] ([hazard_category]).
Regulatory severity: [severity_raw]. Distribution: [distribution_countries].
Description: [description]
```

### שלב 7 — דירוג בייצור (Production ranking)

מערכת תפעולית שמדרגת **כל ריקול חדש** בזמן אמת (או ב-batch יומי), בלי זוגות LLM:

1. **איסוף** — ריקול נכנס מ-FDA / FSIS / FSA UK (או RASFF בעתיד).
2. **ייצוג** — Natural Template מאותם שדות כמו באימון.
3. **ציון** — Bi-Encoder מחזיר `score` מספרי אחד לריקול.
4. **תעדוף** — מיון מול מאגר אחרונים / אחוזון (percentile) בדגימת הייחוס.
5. **סף התראה** — ריקול מעל threshold (או top-K ביום) → דיגסט למשרד הבריאות / דשבורד.

מטרה עסקית: MOH רואה רק מה שדורש התייחסות — לא 18,000 רשומות גולמיות.

### שלב 8 — הסבריות עם Counterfactuals

לאחר שיש מודל שמדרג, בודקים **למה** ריקול קיבל ציון גבוה — דרישה קריטית לרגולטור:

1. בוחרים ריקול שדורג גבוה (או נמוך).
2. משנים **פרמטר אחד** בכל ניסוי בטקסט (למשל: `distribution_countries` → ישראל, או הוספת "Listeria", או Class I → Class III).
3. מריצים שוב את ה-Bi-Encoder ורואים שינוי ב-`score`.
4. הפרמטרים שמזיזים את הציון הכי הרבה = **גורמי הסבר** אינטואיטיביים למצגת MOH.

דוגמה: "אם מחליפים RTE → מוצר שדורש בישול, הציון יורד ב-X" — מחזק אמון במערכת מעבר ל-black box.

---

## 6. מקורות הנתונים

### מקורות פעילים בפרויקט (3)

| מקור | אזור | סוג | סטטוס |
|---|---|---|---|
| FDA Recall Enforcement Reports (openFDA) | ארה"ב | API מלא, JSON | פעיל — 15,947 רשומות |
| USDA FSIS Recall API | ארה"ב (בשר/עוף) | API + curl_cffi bypass | פעיל — 909 רשומות |
| FSA UK Food Alerts API | בריטניה | API מלא, JSON | פעיל — 1,314 רשומות |
| RASFF Window | אירופה | UI scraping בלבד | נדחה ל-post-MVP |

### Endpoints ופרטים טכניים

```
FDA Enforcement:
  endpoint: https://api.fda.gov/food/enforcement.json
  docs:     https://open.fda.gov/apis/food/enforcement/
  auth:     none required
  format:   JSON
  records:  ~28,774 historical
  update:   weekly

USDA FSIS:
  endpoint: https://www.fsis.usda.gov/fsis/api/recall/v/1
  docs:     https://www.fsis.usda.gov/science-data/developer-resources/recall-api
  auth:     none required
  format:   JSON
  records:  ~2,000 historical (entire history in one response)
  note:     Akamai bot protection requires TLS fingerprint spoofing.
            We use curl_cffi with impersonate="chrome120" to bypass it.
            Verified working from Israeli IP on 2026-05-18.

FSA UK:
  endpoint: https://data.food.gov.uk/food-alerts/id
  docs:     https://data.food.gov.uk/food-alerts/ui/reference
  auth:     none required
  format:   JSON
  records:  AA (Allergy Alerts), PRIN (Product Recall), FAFA (Food Alert for Action)
```

### מקורות נוספים מהבריף שאינם בהיקף ה-MVP

הוצגו ברשימה הרשמית אך לא נכללים בשלב הנוכחי (יישקלו בהמשך):

- FDA Import Alerts (אין API פתוח, דורש FDA Data Dashboard auth key)
- FDA Safety Alerts (HTML בלבד)
- FDA CARES / CAERS (יחידת רישום שונה — דיווחי אירועים שליליים, לא ריקולים)
- FDA CORE Outbreaks (HTML בלבד)
- RASFF Window (אין API פתוח, דורש EU Login)
- INFOSAN (קהילה סגורה, גישה במייל בלבד)
- CDC outbreaks (RSS אגרגטור)
- USDA outbreak investigations (HTML בלבד)
- WHO News, EFSA, EFSA Journal, US Federal Register (RSS / scientific publications)

הסיבה לצמצום ל-3: כולם API נקיים ללא אימות, מחזירים JSON, ויחידת הרישום אחידה (ריקול אחד = שורה אחת).

---

## 7. סכמת הנתונים

### Core schema (25 עמודות)

יחידת הרישום: ריקול אחד = שורה אחת. כפילויות בין מקורות לא נמזגות אלא נקשרות דרך `fingerprint`.

```sql
-- Identity & dedup
id                       TEXT PRIMARY KEY     -- internal UUID-like
source_id                TEXT NOT NULL        -- enum: fda_enforcement | fsis | fsa_uk
source_record_id         TEXT NOT NULL        -- ID במקור
fingerprint              TEXT NOT NULL        -- hash for cross-source dedup

-- Provenance
record_url               TEXT                 -- direct link to source record
ingestion_date           TEXT NOT NULL        -- when we collected it
source_published_date    TEXT                 -- when source published it

-- Time
event_initiation_date    TEXT                 -- when recall opened
event_status             TEXT                 -- ongoing | completed | terminated

-- Geography
origin_country           TEXT
distribution_countries   TEXT                 -- JSON array
israel_relevance_flag    INTEGER DEFAULT 0    -- boolean

-- Company / supply chain
recalling_firm           TEXT
brand_names              TEXT                 -- JSON array

-- Product
product_description      TEXT                 -- free text
product_category         TEXT                 -- controlled vocab

-- Hazard
hazard_category          TEXT                 -- biological | chemical | physical | allergen | fraud | regulatory
hazard_specific          TEXT                 -- e.g. "Listeria monocytogenes"

-- Severity
severity_raw             TEXT                 -- raw label from source (Class I, AA, FAFA)
severity_normalized      TEXT                 -- enum: high | medium | low

-- Population & impact
population_at_risk       TEXT                 -- general | infants | elderly | allergic | immunocompromised
illness_count_reported   INTEGER

-- Free text
title                    TEXT                 -- short headline
description              TEXT                 -- full body text
reason_for_recall        TEXT                 -- violation reason
```

### Extension fields (יתווספו בהמשך)

- שרשרת אספקה מורחבת: manufacturer, distributor, lot_numbers
- workflow: review_status, notification_sent
- Bradley-Terry scores: bt_severity_score, bt_likelihood_score, bt_exposure_score, bt_composite_score
- Classification metadata: classification_method, classification_confidence
- Impact מורחב: death_count, hospitalization_count

### טבלאות עזר

- `ingestion_runs` — לוג ריצות לכל מקור (observability + idempotency)
- `sample_members` — חברות בדגימות סטרטיפיות לתיוג
- `labeling_pairs` — זוגות נבחרים לתיוג, עם קטגוריה (same/adjacent/polar/cross-source)
- `llm_labels` — תוויות LLM לכל (pair × dimension × order), עם reasoning ו-model
- `expert_labels` — תוויות מומחי משרד הבריאות (subset של זוגות)

---

## 8. מצב נוכחי

### עדכון אחרון — 2026-06-08

**שלב 6 (Bi-Encoder) — הרצה מלאה הושלמה (28.05.2026).** המודל אומן על כל מערך הזוגות (לא רק הפיילוט):

| פרמטר | ערך |
|---|---|
| Backbone | `distilroberta-base` |
| Train / Test | 34,322 / 2,115 זוגות |
| Epochs / Batch / Device | 3 / 16 / MPS |
| זמן ריצה | 40,879 שנ׳ (~11.4 שעות) |
| **Best test pairwise accuracy** | **68.7%** (epoch 1) |

**ממצא חשוב — overfitting:** הדיוק הטוב ביותר הושג כבר ב-epoch 1 (0.687). ב-epochs 2–3 ה-train_loss המשיך לרדת (0.221 → 0.069) אך ה-test_loss עלה (1.42 → 1.81) והדיוק ירד (0.662 / 0.664). המודל השמור (`best_model.pt`) הוא של epoch 1. ההרצה המלאה כמעט לא שיפרה את הפיילוט (67.4% → 68.7%). **מסקנה לעבודה הבאה:** epoch אחד מספיק; לשקול early-stopping, dropout/weight-decay גבוה יותר, או backbone גדול יותר. הקבצים והפקודות ב-`docs/STEP6_BI_ENCODER_RUNBOOK.md` (הרנבוק עדיין מתאר את הפיילוט וטעון עדכון).

**אימות מומחים — נסגר כשאלון 5 זוגות.** תיוג מומחים מלא (100 זוגות ל-MOH) **בוטל**. במקומו בוצע שאלון איכותני על 5 זוגות (`expert_review_2026-05-18.json` / `expert_review.html`) — ראה שלב 2. `expert_labels` נשארת ריקה במכוון.

**עדיין לא רץ:** שלב 7 (ציון כל המאגר + percentile/threshold — `scripts/score_alerts.py` טרם הופעל, אין קבצי `bi_encoder_scores_*.json`), בייסליינים (severity_raw, TF-IDF), שלב 8 (counterfactuals).

### מה נבנה ועובד (נכון ל-2026-05-11)

- מבנה פרויקט: `src/`, `scripts/`, `data/`
- סכמה ב-SQLite מעודכנת (`src/schema.sql`) — 5 טבלאות
- 3 קולקטורים מלאים: FDA Enforcement, USDA FSIS, FSA UK
- מודולי dedup, sample, pipeline
- מודול labeling: pair_selection, prompts (template + system prompt)
- Scripts CLI: `scripts/ingest.py`, `scripts/build_sample.py`, `scripts/select_pairs.py`

### מה יש בדאטה בייס (2026-05-18, 10-year window)

- 15,947 רשומות מ-FDA Enforcement (2012-2026)
- 909 רשומות מ-USDA FSIS (2016-2026) — הרצנו דרך curl_cffi עם chrome impersonation לעקוף Akamai
- 1,314 רשומות מ-FSA UK (2018-2026)
- סך הכל **18,170 רשומות**

### דגימה סטרטיפית של 500 (`labeling_v3`)

| Severity | סך | FDA | FSIS | FSA UK |
|---|---|---|---|---|
| high   | 167 | 94 | 58 | 15 |
| medium | 167 | 56 | 55 | 56 |
| low    | 166 | 146 | 20 | 0  |

הערה: stratum ה-low הוא 100% FDA + FSIS. FSA UK לא מסווג low — האלרטים שלהם כולם PRIN/AA/FAFA שממופים ל-medium/high.

פיזור על שנים: 2014-2026, כשהשנים 2017-2018 (66-76 רשומות) ו-2023-2025 (45-60) הן הצפופות ביותר.

### זוגות נבחרים לתיוג (299 זוגות)

| קטגוריה | מספר זוגות | מטרה |
|---|---|---|
| same_severity_high | 33 | הבחנות עדינות בתוך high |
| same_severity_medium | 33 | הבחנות עדינות בתוך medium |
| same_severity_low | 33 | הבחנות עדינות בתוך low |
| adjacent_high_medium | 50 | זוגות שכנים על הציר |
| adjacent_medium_low | 50 | זוגות שכנים על הציר |
| polar_high_low | 50 | אימות קל (קצה לקצה) |
| cross_source_high | 25 | רובסטיות בין מקורות |
| cross_source_medium | 25 | רובסטיות בין מקורות |

---

## 9. שאלות פתוחות

### 9.1 הרצת FSIS ממיקום אחר

הקוד של FSIS שלם, אבל לא נבדק כי הרשת מחסומת על ידי Akamai. צריך להריץ פעם אחת מבית או ממובייל הוטספוט כדי לאמת שמות שדות וטעינה מלאה.

### 9.2 חילוץ hazard_category לכל הרשומות

84% מהרשומות בדגימה ללא קטגוריית סיכון. אופציות:
- חילוץ מבוסס מילות מפתח (כמו שיש כבר בקולקטור FSA UK)
- שיחה ל-LLM לסיווג
- שילוב — heuristic ראשון, LLM ל-edge cases

החלטה זו צריכה להתקבל לפני שלב 2.

### 9.3 הגדרה אופרטיבית של "מסוכן יותר" — נסגר

הוחלט:
- מי מתייג: Claude Sonnet 4.6 על כל 299 הזוגות. אימות אנושי **צומצם** מ-100 זוגות לשאלון איכותני על **5 זוגות** (`expert_review_2026-05-18.json`) — תיוג מומחים מלא לא יתבצע.
- איזה LLM: **Claude Sonnet 4.6** (איזון מחיר/ביצועים).
- prompt: נכתב ב-`src/labeling/prompts.py`. עוגן ל-21 CFR 7.41.

### 9.4 בחירת זוגות לתיוג — נסגר

האלגוריתם המלא ב-`src/labeling/pair_selection.py`. 299 זוגות ב-8 קטגוריות עם stratification חכם.

### 9.5 שילוב הציונים בין הממדים — נסגר

**ממוצע שווה:** `composite = (severity + likelihood + exposure) / 3`. מיושם ב-DB. Bootstrap+IVW נשאר כהצעה אקדמית מ-11.05 אך לא יושם ב-MVP.

### 9.6 ארכיטקטורת המודל המלמדת — נסגר

**Bi-Encoder (Siamese)** + **BCE על הפרש הציונים** `score_A - score_B`. לא Cross-Encoder, לא Margin Loss. תוויות אימון מזוגות סינתטיים לפי composite BT (שלב 5).

---

## 10. בסיס מתודולוגי

### מאמרים ליבה (ב-`references/papers/`)

- **FAO_food_safety_risk_ranking.pdf** — מסגרת FAO לדירוג סיכוני בטיחות מזון. שלושה שלבים: הגדרת היקף, פיתוח גישה, ביצוע. ממדי סיכון: likelihood ו-severity. רלוונטי ל-RiskScorer.

- **Kaplan_Garrick_1981_risk_definition.pdf** — ההגדרה הכמותית של סיכון כ"קבוצת שלשות": (תרחיש, הסתברות, השלכה). הבחנה תיאורטית בין risk, hazard, ו-uncertainty.

- **Rudin_2022_interpretable_scoring_systems.pdf** — מערכות ציון ניתנות לפירוש. דוגמת 2HELPS2B מראה איך מודל ML יכול להיות פשוט ושקוף כמו מערכת ניקוד אנושית. רלוונטי לדרישת ההסבריות.

- **UKHSA_2024_LLMs_for_public_health.pdf** — שימוש ב-LLMs לסיווג ולחילוץ טקסט בבריאות הציבור.

- **HFES_2023_patient_safety_events_NLP.pdf** — סיווג אירועי בטיחות מטופלים עם NLP. כללי, לא ספציפי לבטיחות מזון.

### קריאת חובה מהסילבוס (קורס 55910)

- Powell, S.J. and Batt, R.J. (2011). *Modeling for Insight: A Master Class for Business Analysts*. Wiley.
- Provost, F. and Fawcett, T. (2013). *Data Science for Business*. O'Reilly.

---

## 11. תוצרים מצופים

### לפי הבריף הרשמי (4 תוצרים)

1. **מערכת מודיעין פעילה** — איסוף, סינון, תעדוף, סיווג, זיהוי דפוסים.
2. **התראות וסקירות תקופתיות** — דיגסטים יומי/שבועי/חודשי במייל + push לאירועים קריטיים + ארכיון.
3. **תיעוד טכני וההכנה להעברה** — קוד מתועד, ארכיטקטורה, מדריך התקנה/הפעלה/תחזוקה, בשיתוף IT המשרד.
4. **תוצר אקדמי** — עבודה כתובה + מצגת מול הספונסר והכיתה.

### חלוקת ציון בקורס

- מבחן בעל פה: 40%
- מצגת: 20%
- כתיבה / תוצרים: 30%
- השתתפות: 10%
- נוכחות חובה: 80%

---

## 12. צעדים הבאים (priority order)

### הושלם ✓

1. איסוף ~18,170 ריקולים (FDA, FSIS, FSA UK).
2. דגימה `labeling_v3` — 500 ריקולים.
3. תיוג LLM — 299 זוגות × 3 ממדים (Claude Sonnet 4.6).
4. Bradley-Terry — severity / likelihood / exposure + **composite ממוצע שווה** (330 ריקולים עם ציון).
5. דוח HTML + ייצוא Excel לשיתוף.

### הושלם — המשך

6. ~~**אימות מומחים**~~ ✓ — נסגר כ**שאלון 5 זוגות** (`expert_review_2026-05-18.json`); תיוג מומחים מלא בוטל.
7. ~~**זוגות אימון סינתטיים**~~ ✓ — `scripts/generate_training_pairs.py`: 34,322 train + 2,115 test pairs (330 scored alerts, split 80/20 stratified).
8. ~~**train/test split**~~ ✓ — ברמת alert ב-`training_split_members` (seed=42).
9. ~~אימון **Bi-Encoder** (הרצה מלאה)~~ ✓ — 34,322/2,115 זוגות, 3 epochs, **68.7%** pairwise acc (epoch 1; overfitting אחריו); מודל ב-`models/bi_encoder_labeling_v3/`.

### מיידי — הרצה

10. **שלב 7** — הריצי `scripts/score_all_alerts.py` לציון כל 18,170 הריקולים.
    - דרוש: `python3 -m pip install -r requirements-ml.txt` (כולל scipy, scikit-learn).
    - פלט: `data/all_alert_scores.json` + טבלת `alert_scores` ב-DB.
11. **שלב 7ב** — הריצי `scripts/rank_daily.py` לדיגסט HTML+JSON (אחרי שלב 7).
12. **שלב 8** — הריצי `scripts/counterfactuals.py` לניתוח הסבריות (אחרי שלב 7).
13. דשבורד / דיגסט MOH, תיעוד, מצגת.

### חוב טכני שצריך לטפל בו

- **Overfitting ב-Bi-Encoder** — epoch 1 הוא הטוב ביותר; להוסיף early-stopping / רגולריזציה, או לנסות backbone גדול יותר.
- הרצת FSIS ממיקום ללא חסימת Akamai (דורש VPN אמריקאי או מיקום מחוץ לישראל).
- enrichment של hazard_category על FDA records.
- חיפוש המאמר מ-Northeastern University על 400K מסמכים רגולטוריים שהמרצים הציעו.
- יצירת קשר עם CTO/DTO ב-FSA UK להבין מה הם עושים.

### ניקוי מאגר — בוצע ב-2026-06-08 ✓

נמחקו קבצים כפולים/מיושנים:
- `Papers/` (זהה ל-`references/papers/`), ו-3 עותקי שורש (`project_brief.docx`, `project_pitch_deck.pptx`, `initial_sources_list.xlsx`) שנשארו ב-`briefing/`.
- `tmp_paper_extract{,2,3}.txt` (דאמפים זמניים מה-PDFs).
- `food_safety_engine.py` (אב-טיפוס מונוליטי ישן שהוחלף ע"י `src/` — RSS/scrape, Trends, OpenAI, מחוץ להיקף).

תוקנו נתיבים ושמות מודל מיושנים ב-`run_labeling.py` (`claude-sonnet-4-5` → `4-6`, נתיב יחסי), `LLM_LABELING_*.md`, ו-`docs/STEP6_BI_ENCODER_RUNBOOK.md` (גם עודכן לתוצאות ההרצה המלאה).

נשמר במכוון: `food-safety-dashboard.jsx` — דשבורד React על דאטה **מדומה** ורשימת מקורות ישנה (12 מקורות, כולל Trends/חקירות מחוץ להיקף). שמור כ-mockup אפשרי למצגת; אינו מחובר ל-DB.

---

## 13. המלצות לשיפור דיוק ה-Bi-Encoder (ממתינות לפידבק מרצים)

עודכן: 2026-06-08. המלצות אלו מחכות להערות המרצים לפני יישום.

### הבעיה המרכזית

264 ריקולי אימון מול מודל של 82M פרמטרים — יחס לא מאוזן. כל שיפור אחר הוא ריפוי סימפטומים עד שיבוא פתרון לכמות הנתונים.

### אפשרות 1 — רגולריזציה (שינוי קוד, ללא נתונים חדשים)

שינויים ב-`src/models/bi_encoder.py` ו-`scripts/train_bi_encoder.py`:

```python
# dropout גבוה יותר על הראש (עכשיו 0.1 — לנסות 0.3–0.5)
self.dropout = nn.Dropout(0.3)

# weight decay ב-optimizer (עכשיו כנראה 0)
optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

# label smoothing — לפחות ביטחון יתר
labels = labels * 0.9 + 0.05
```

צפי: +1–2% test_acc, בעיקר יסגור פער train/test.

### אפשרות 2 — הקפאת שכבות ה-backbone

במקום לאמן את כל distilroberta (82M פרמטרים), להקפיא רוב השכבות ולאמן רק את הראש ואת 2 השכבות האחרונות:

```python
for param in model.encoder.parameters():
    param.requires_grad = False
for layer in model.encoder.encoder.layer[-2:]:
    for param in layer.parameters():
        param.requires_grad = True
```

צפי: פחות overfitting, זמן אימון קצר יותר (~3 שעות במקום 11). יש לבדוק אם יש שיפור ב-test_acc.

### אפשרות 3 — Early Stopping + Learning Rate Scheduler

```python
from torch.optim.lr_scheduler import CosineAnnealingLR
scheduler = CosineAnnealingLR(optimizer, T_max=n_epochs)

# early stopping: לעצור אם test_loss לא משתפר
best_loss = float('inf')
patience = 2
```

צפי: בעיקר מונע אימון מיותר. ב-run הנוכחי epoch 1 כבר היה הטוב ביותר.

### אפשרות 4 — הרחבת נתונים (הכי משפיעה אם אפשרי)

| אפשרות | עלות | צפי |
|---|---|---|
| הרחב מ-330 ל-600+ ריקולים מוסמנים (הרצת LLM נוספת) | ~₪20 | **הכי גדול** — C(480,2)=114,960 זוגות אימון (×3 מהנוכחי) |
| Data augmentation — ערבב סדר שדות בטמפלייט | חינם | בינוני |
| Synthetic pairs עם margin שונה בין ציוני BT | חינם | קטן |

### אפשרות 5 — Backbone מותאם תחום

| backbone | פרמטרים | יתרון |
|---|---|---|
| `distilroberta-base` (נוכחי) | 82M | מהיר |
| `roberta-base` | 125M | יציב יותר |
| `allenai/biomed_roberta_base` | 125M | אומן על טקסטים ביו-רפואיים |
| `pritamdeka/PubMedBERT-abstract-fulltext` | 110M | מדעי בריאות |

### סדר עדיפויות מוצע (לאחר פידבק מרצים)

1. **Dropout 0.3 + weight_decay 0.01** — 2 שורות קוד, ניסוי של ~11 שעות.
2. **הקפאת backbone** — מוריד זמן אימון ל-~3 שעות, יכול לשפר test_acc.
3. **Data augmentation** על 264 הריקולים הקיימים.
4. אם יש כח — הרחבת נתונים (הרצת LLM על זוגות נוספים).

---

## 14. Changelog

- **2026-06-08** — **RASFF collector נוסף** (`src/collectors/rasff.py`):
  - מקור: RASFF Window public API (ללא authentication) — `POST /rasff-window/backend/public/notification/search/consolidated/`
  - ה-endpoint התגלה מתוך ה-JS bundle של הפורטל; ה-API מחזיר ~31k התראות ב-JSON.
  - שדות: subject, productCategory, notificationClassification, riskDecision, originCountries, ecValidationDate.
  - Severity mapping: riskDecision "serious"→high, "potential risk"→medium, "no risk"→low.
  - Hazard: חילוץ מ-subject text (biological/chemical/allergen/physical).
  - `src/collectors/__init__.py` עודכן — COLLECTORS עכשיו כולל 4 מקורות.
  - **להרצה:** `python3 scripts/ingest.py --sources rasff --days 3650` (כל ההיסטוריה), לאחר מכן re-run generate_training_pairs + train.

- **2026-06-08** — שיפורים בעקבות פגישת מרצים (לב מוצ'ניק + ניקול אדלר):
  - **ארכיטקטורת Bi-Encoder עודכנה:** הוספה שכבת hidden (768→100→1) עם שתי שכבות Dropout(0.3) לפני כל שכבת Linear — מפחית overfitting.
  - **חלוקה ל-3 קבוצות (train/val/test):** הוחלף ה-80/20 בחלוקה 70/15/15. val לבחירת מודל (early stopping), test נגעים פעם אחת בלבד בסוף.
  - **Early stopping:** מאמן עוצר אחרי 2 epochs ללא שיפור ב-val_acc (--patience).
  - **Intra-epoch logging:** loss מודפס כל 50 batches בתוך כל epoch (--log-every).
  - `generate_training_pairs.py` עודכן ל-`--val-frac`, `training_pairs.py` עודכן לשלושה חלקים.
  - **בייסליין חושב ונמדד:** severity_normalized = 66.7%, Bi-Encoder = 68.7% (+2pp). הפער מגיע כולו מ-32% הזוגות בתוך אותה דרגת severity.
- **2026-06-08** — שלבים 7, 7ב, 8 — **סקריפטים נכתבו, ממתינים להרצה:**
  - `scripts/score_all_alerts.py` — ציון כל 18,170 ריקולים + בייסליינים (severity_raw, TF-IDF) + טבלת `alert_scores` ב-DB.
  - `scripts/rank_daily.py` — pipeline יומי: חלון 30 יום → percentile בחלון → Critical/High/Medium → digest JSON + HTML בעברית.
  - `scripts/counterfactuals.py` — 10 פרטורבציות לכל ריקול (hazard, severity, distribution, RTE) → Δscore לכל שינוי → מסביר למה ריקול דורג גבוה.
  - `docs/STEPS7_8_RUNBOOK.md` נוצר עם הוראות הרצה.
  - `requirements-ml.txt` עודכן: הוספו scipy, scikit-learn.
- **2026-06-08** — נוסף סעיף 13: המלצות לשיפור דיוק Bi-Encoder (ממתינות לפידבק מרצים) — רגולריזציה, הקפאת backbone, early stopping, הרחבת נתונים, backbone מותאם תחום.
- **2026-06-08** — סקירת מאגר מלאה ועדכון סטטוס:
  - **שלב 6 — הרצה מלאה הושלמה (28.05):** 34,322/2,115 זוגות, 3 epochs, **68.7%** pairwise acc (epoch 1), עם overfitting אחריו. עודכן סעיף 8.
  - **אימות מומחים נסגר כשאלון 5 זוגות** — תיוג מומחים מלא בוטל; `expert_labels` נשארת ריקה במכוון. עודכנו סעיפים 5 (שלב 2), 9.3, ו-12.
  - **ניקוי מאגר בוצע:** נמחקו `Papers/`, 3 עותקי שורש (docx/pptx/xlsx), `tmp_paper_extract{,2,3}.txt`, ו-`food_safety_engine.py`.
  - **תוקנו נתיבים/שמות מודל מיושנים:** `run_labeling.py` (`sonnet-4-5`→`4-6`, נתיב יחסי), `LLM_LABELING_*.md`, והרנבוק (גם עודכן לתוצאות ההרצה המלאה).

- **2026-05-25** — שלב 6 (Bi-Encoder, פיילוט):
  - `src/models/bi_encoder.py`, `pair_dataset.py`, `scripts/train_bi_encoder.py`, `scripts/score_alerts.py`.
  - `requirements-ml.txt`; אימון על MPS: 2 epochs, 3k/500 pairs → test pairwise acc **0.674**.

- **2026-05-21** — שלב 5 (זוגות סינתטיים):
  - `src/labeling/training_pairs.py`, `scripts/generate_training_pairs.py`.
  - 330 ריקולים עם composite → 264 train / 66 test alerts → 34,322 / 2,115 זוגות.
  - ייצוא: `data/synthetic_training_pairs.json`, CSV ב-`data/exports/training_pairs/`, טבלאות DB.

- **2026-05-21** — עדכון מתודולוגיה ב-`PROJECT.md`:
  - שלב 4: **ממוצע שווה** ל-composite (לא Bootstrap+IVW); מיושם ב-`bt_scores`.
  - שלב 5: תווית זוג = מי עם **composite BT גבוה יותר**.
  - שלב 6: **Bi-Encoder + BCE על הפרש ציונים** (לא Margin Loss).
  - שלבים 7–8: הרחבת הסבר על דירוג בייצור ו-counterfactuals.
  - צעדים הבאים עודכנו לפי סטטוס בפועל.

- **2026-05-18** — הרחבה משמעותית של המאגר:
  - FSIS נפתר! curl_cffi עם chrome120 impersonation עוקף את Akamai bot protection.
  - הרצנו את כל 3 המקורות עם חלון של 10 שנים → 18,170 רשומות (פי 3.5 מהקודם).
  - דגימה חדשה `labeling_v3` עם 500 ריקולים, פיזור מצוין על severity ועל 3 מקורות.
  - 299 זוגות חדשים נבחרו מ-labeling_v3.
  - RASFF נבדק שוב — חסום ברמת אפליקציה (לא TLS). נדחה ל-post-MVP, יבוצע ב-Selenium או export ידני.

- **2026-05-11** — עדכון מתודולוגי גדול בעקבות פגישת המרצים:
  - שאלת המחקר נוסחה מחדש (פחות LLM-centric).
  - דגימה הוגדלה מ-100 ל-500 ריקולים.
  - ingestion הורחב ל-3 שנים אחורה, 5,088 רשומות במאגר.
  - ממוצע משוקלל הוחלף ב-Bootstrap + Inverse Variance Weighting.
  - Cross-Encoder הוחלף ב-Bi-Encoder (Siamese).
  - נוסף שלב 8 — Counterfactuals להסבריות.
  - נבנה מודול labeling עם pair selection ו-prompt template.
  - נבחר Claude Sonnet 4.6 כ-LLM Judge.
  - 299 זוגות נבחרו ב-8 קטגוריות אסטרטגיות.
- **2026-05-04** — מסמך פרויקט מרכזי נוצר. סוכמו ההחלטות מהפגישות וההתקדמות הטכנית. הוקם הצינור הבסיסי, נטענו 1,827 רשומות, נבנתה דגימת 100 לתיוג.
- **2026-04-27** — שיעור: הוחלט על Bradley-Terry ו-Cross-Encoder כמתודולוגיה.
- **2026-03-29** — פגישה ראשונה: הוגדרה שאלת המחקר המעודכנת, סוקרו מקורות מידע ראשונים.
- **2026-03-23** — פיץ' דק רשמי של הספונסר.
