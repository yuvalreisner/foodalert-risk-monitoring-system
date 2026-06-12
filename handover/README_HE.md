# FoodSafe Intelligence — מדריך הפעלה למשרד הבריאות

**מערכת מודיעין גלוי לבטיחות מזון**  
פותחה במסגרת פרויקט גמר MBA בביג דאטא, האוניברסיטה העברית בירושלים  
בחסות המחלקה לניהול סיכוני מזון, משרד הבריאות

---

## מה המערכת עושה?

המערכת אוספת אוטומטית התראות בטיחות מזון מארבעה מקורות רשמיים:
- **FDA** (ארה"ב) — כ-16,000 ריקולים
- **USDA FSIS** (ארה"ב) — מוצרי בשר ועוף
- **FSA UK** (בריטניה) — התראות מזון בריטיות
- **RASFF** (האיחוד האירופי) — מערכת ההתראות האירופית

לכל התראה מחושב ציון סיכון על ידי מודל בינה מלאכותית (Bi-Encoder מבוסס DistilRoBERTa/BERT), ומיוצר **דשבורד HTML** יומי הניתן לפתיחה בכל דפדפן.

---

## מבנה התיקיות

```
foodsafe_intelligence/
├── README_HE.md          ← המדריך הזה
├── INSTALL.md            ← הוראות התקנה טכניות
├── requirements.txt      ← חבילות Python נדרשות
├── src/                  ← קוד הליבה (DB, collectors)
├── scripts/              ← סקריפטי הרצה
│   ├── ingest.py              איסוף נתונים חדשים
│   ├── score_all_alerts.py    ניקוד ה-AI
│   ├── generate_dashboard.py  יצירת הדשבורד
│   └── rank_daily.py          דיגסט יומי בעברית
├── models/               ← המודל המאומן (לא לשנות!)
│   └── bi_encoder_labeling_v3/
│       ├── best_model.pt      ← המשקולות של המודל (314MB)
│       └── encoder/           ← בסיס DistilRoBERTa
└── data/
    └── alerts.db              ← בסיס הנתונים (SQLite)
```

---

## הרצה יומית — שלושה פקודות בלבד

פתח Terminal (Mac/Linux) או Command Prompt (Windows) מתוך תיקיית הפרויקט:

```bash
# שלב 1: אסוף התראות חדשות (5–15 דקות)
python3 scripts/ingest.py

# שלב 2: נקד את ההתראות החדשות
python3 scripts/score_all_alerts.py

# שלב 3: צור דשבורד מעודכן
python3 scripts/generate_dashboard.py --window 90 --out reports/dashboard_today
```

לאחר מכן פתח את הקובץ `reports/dashboard_today.html` בדפדפן — Firefox / Chrome / Edge.

---

## פרמטרים שאפשר לשנות

```bash
# חלון זמן שונה (למשל 30 יום במקום 90)
python3 scripts/generate_dashboard.py --window 30

# תאריך עבר (לבדיקה של יום ספציפי)
python3 scripts/generate_dashboard.py --date 2026-05-01

# שם קובץ פלט
python3 scripts/generate_dashboard.py --out reports/dashboard_june
```

---

## תזמון אוטומטי (הרצה כל בוקר)

### Linux/Mac — cron job
```bash
# פתח עורך cron:
crontab -e

# הוסף שורה זו (מריץ כל יום ב-06:00):
0 6 * * * cd /opt/foodsafe && python3 scripts/ingest.py && python3 scripts/score_all_alerts.py && python3 scripts/generate_dashboard.py --window 90 --out reports/dashboard_today
```

### Windows — Task Scheduler
1. פתח "Task Scheduler" → "Create Basic Task"
2. שם: `FoodSafe Daily`
3. Trigger: Daily, 06:00
4. Action: Start a program → `python3`
5. Arguments: `scripts\generate_dashboard.py --window 90`
6. Start in: `C:\path\to\foodsafe_intelligence`

---

## הדשבורד — מה רואים?

| סקשן | תוכן |
|---|---|
| 🇮🇱 Israel Watch | התראות שישראל מוזכרת בהן — תמיד ראשון |
| 🔴 Critical | top 5% מהתראות החלון — הדחופות ביותר |
| 🟠 High | top 5–20% — סיכון גבוה |
| 🟡 Medium | top 20–50% — סיכון בינוני |
| 📈 Trends | גרף טרנד 13 חודשים לפי סוג הסיכון |
| 📊 Breakdowns | פירוק לפי סוג מזון, מדינת מקור, מקור הנתונים |
| ℹ️ About | הסבר המתודולוגיה, מקורות, מגבלות |

### ציון הסיכון (X.X/10)
ציון אבסולוטי שמחושב על ידי מודל ה-AI. מנורמל לסקאלה קבועה (1–10):
- **8–10**: חריג ביותר, בין 5% הגרועים שנראו
- **6–8**: סיכון גבוה
- **4–6**: סיכון בינוני
- **1–4**: סיכון נמוך

---

## מגבלות ידועות

1. **כיסוי ישראל**: הסימון "רלוונטי לישראל" מבוסס על אזכור טקסטואלי בלבד. לא מתחבר לרישום היבוא הישראלי. המלצה לעתיד: חיבור לנתוני יבוא מ-YALAG/מינהל המכס.

2. **RASFF לא היה בנתוני אימון**: המודל אומן על FDA/FSIS/FSA בלבד. ציוני RASFF פחות מכוילים — ניתן לשפר בגרסה הבאה.

3. **FDA אין permalink**: לריקולי FDA אין URL ישיר לדף הספציפי. הדשבורד מציג קישור ל-API הרשמי + חיפוש לפי שם החברה.

---

## שאלות טכניות

לפניות טכניות ניתן לפנות לצוות הפיתוח:
- **יובל ריסנר** — yuvalreisner96@gmail.com
- **נוי / יובלי** — [להשלים]

---

*FoodSafe Intelligence v1.0 · Hebrew University of Jerusalem MBA Capstone 2026*
