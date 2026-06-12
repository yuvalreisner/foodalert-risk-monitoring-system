# שלבים 7, 7ב, 8 — Runbook

עדכון: 2026-06-08

---

## סקירה

| שלב | סקריפט | פלט |
|---|---|---|
| 7 — ציון כל המאגר | `scripts/score_all_alerts.py` | `data/all_alert_scores.json` + טבלת `alert_scores` ב-DB |
| 7ב — pipeline יומי | `scripts/rank_daily.py` | `reports/digest_YYYY-MM-DD.json` + `.html` |
| 8 — Counterfactuals | `scripts/counterfactuals.py` | `reports/counterfactuals.json` |

---

## התקנת תלויות (פעם אחת)

```bash
cd /Users/yuvalreisner/Play_ground/mba_Big_data_project
python3 -m pip install -r requirements-ml.txt
```

כולל: `torch`, `transformers`, `accelerate`, `scipy`, `scikit-learn`

---

## שלב 7 — ציון כל 18,170 הריקולים

```bash
python3 scripts/score_all_alerts.py
```

הסקריפט:
1. טוען את `models/bi_encoder_labeling_v3/best_model.pt`
2. מדרג **כל** הריקולים מ-DB (לא רק ה-330 מהאימון)
3. מחשב שלושה ציונים לכל ריקול:
   - `bi_encoder_score` — ציון הMI-Encoder (המודל שלנו)
   - `severity_baseline` — ממפה severity_raw למספר (Class I=1.0, Class II=0.6 וכו')
   - `tfidf_score` — קוסינוס דמיון לשאלת "סיכון גבוה" (TF-IDF)
4. מדפיס Spearman correlation מול כל בייסליין
5. שומר `data/all_alert_scores.json` + טבלת `alert_scores` ב-DB

**תוצאה צפויה (~18 דקות על MPS):**
```
Top 10 alerts by Bi-Encoder score:
  +X.XXXX  pct=0.99  Class I  fda_enforcement  Listeria in RTE cheese...
  ...
Spearman(Bi-Encoder, severity_raw_baseline) = X.XXX  p=X.Xe-XX
Spearman(Bi-Encoder, TF-IDF)               = X.XXX  p=X.Xe-XX
```

**אם אין scikit-learn / scipy** — ממשיך בלי TF-IDF / בלי קורלציה:
```bash
python3 scripts/score_all_alerts.py --no-tfidf
```

---

## שלב 7ב — Digest יומי ל-MOH

**דרישה:** שלב 7 חייב לרוץ לפני כן (טבלת `alert_scores` חייבת להיות מאוכלסת).

```bash
# Digest של 30 הימים האחרונים (ברירת מחדל)
python3 scripts/rank_daily.py

# חלון של 60 יום
python3 scripts/rank_daily.py --window 60

# כנקודת זמן היסטורית
python3 scripts/rank_daily.py --date 2026-05-01

# רק קריטי + גבוה (ללא בינוני)
python3 scripts/rank_daily.py --min-tier high
```

**פלט:**
- `reports/digest_YYYY-MM-DD.json` — מידע מובנה לכל ריקול בחלון
- `reports/digest_YYYY-MM-DD.html` — דוח HTML בעברית לMOH

**סף האחוזונים (בתוך החלון):**

| רמה | אחוזון בחלון | פעולה |
|---|---|---|
| 🔴 קריטי | top 5% (≥0.95) | התראה מיידית |
| 🟠 גבוה | 5–20% (≥0.80) | דיגסט יומי |
| 🟡 בינוני | 20–50% (≥0.50) | דיגסט שבועי |
| ⚪ נמוך | bottom 50% | ארכיון |

**לוגיקת החלון:** רק ריקולים שה-`source_published_date` שלהם בחלון הזמן.
האחוזון מחושב **בתוך** החלון (לא גלובלי) — כך שתמיד יש ריקולים בכל רמה.

---

## שלב 8 — Counterfactuals להסבריות

**דרישה:** שלב 7 חייב לרוץ לפני כן.

```bash
# ניתוח top 5 + bottom 2
python3 scripts/counterfactuals.py

# top 10
python3 scripts/counterfactuals.py --n 10

# ריקול ספציפי
python3 scripts/counterfactuals.py --alert-id "fda_enforcement::F-1671-2024"
```

**10 פרטורבציות לכל ריקול:**

| פרטורבציה | שאלה שנבדקת |
|---|---|
| hazard→Listeria | האם הסיכון (ליסטריה) מעלה את הציון? |
| hazard→mineral_oil | האם החלפה לסיכון כרוני מוריד? |
| hazard→allergen | האם אלרגן לא מוצהר מעלה? |
| severity→Class I | האם עדכון חומרה ל-Class I מעלה? |
| severity→Class III | האם הורדה ל-Class III מורידה? |
| dist→nationwide | האם הפצה ארצית מעלה? |
| dist→local_only | האם הגבלה למקומי מורידה? |
| dist→+Israel | האם הוספת ישראל מעלה? |
| rte→RTE | האם ציון "ready-to-eat" מעלה? |
| rte→cooked | האם ציון "דורש בישול" מוריד? |

**פלט לדוגמה:**
```
Alert: Cheese recalled for Listeria contamination...
  score=+2.1234  pct=98.7%
  perturbation                   delta     before →    after
  --------------------------------  --------  --------- → ---------
  ↓ hazard→mineral_oil          -0.4123   +2.1234 → +1.7111
  ↑ dist→+Israel                +0.0891   +2.1234 → +2.2125
  → hazard→Listeria             +0.0012   +2.1234 → +2.1246  (כבר ליסטריה)
  ...
→ Largest driver: hazard→mineral_oil  Δ=-0.4123
```

---

## סדר הרצה מלא

```bash
# 1. התקן תלויות (אם לא הותקנו)
python3 -m pip install -r requirements-ml.txt

# 2. שלב 7 — ציון המאגר (~18 דק')
python3 scripts/score_all_alerts.py

# 3. שלב 7ב — digest יומי
python3 scripts/rank_daily.py

# 4. שלב 8 — counterfactuals (~2 דק')
python3 scripts/counterfactuals.py --n 5
```

---

## קבצי פלט

```
data/
  all_alert_scores.json          # כל 18k ציונים

reports/
  digest_YYYY-MM-DD.json         # דיגסט JSON
  digest_YYYY-MM-DD.html         # דיגסט HTML לMOH
  counterfactuals.json           # ניתוח הסבריות
```
