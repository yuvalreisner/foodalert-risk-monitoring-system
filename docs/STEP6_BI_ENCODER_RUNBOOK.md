# שלב 6 — Bi-Encoder · פיילוט + הרצה מלאה (הושלמה)

עדכון: 2026-06-08

## הרצה מלאה — הושלמה ✓ (28.05.2026)

המקור: `training_metrics.json` + `full_training.log`.

| פריט | ערך |
|------|-----|
| מכשיר | Apple **MPS** |
| Backbone | `distilroberta-base` |
| Train / test | **34,322 / 2,115** זוגות (מלא) |
| Epochs / Batch | 3 / 16 |
| זמן | 40,879 שנ׳ (~11.4 שעות) |
| **Best test pairwise accuracy** | **68.7%** (epoch 1) |
| מודל שמור | `models/bi_encoder_labeling_v3/best_model.pt` (epoch 1) |

**Overfitting:** epoch 1 הוא הטוב ביותר. אחריו ה-train_loss ממשיך לרדת אך ה-test_loss עולה:

| Epoch | train_loss | test_loss | test_acc |
|---|---|---|---|
| 1 | 0.221 | 1.419 | **0.687** |
| 2 | 0.092 | 1.804 | 0.662 |
| 3 | 0.069 | 1.813 | 0.664 |

**מסקנה:** epoch אחד מספיק. לעבודה הבאה — early-stopping, dropout/weight-decay גבוה יותר, או backbone גדול יותר. ההרצה המלאה כמעט לא שיפרה את הפיילוט (67.4% → 68.7%).

## פיילוט (היסטורי, להשוואה)

3,000/500 זוגות · 2 epochs · batch 8 · ~7 דק׳ → test pairwise acc **67.4%**, Spearman 0.42 (p≈0.0004) על 66 ריקולי test מול BT composite.

## להרצה חוזרת

```bash
cd /Users/yuvalreisner/Play_ground/mba_Big_data_project
python3 -m pip install -r requirements-ml.txt
python3 scripts/train_bi_encoder.py --epochs 3 --batch-size 16 2>&1 | tee models/bi_encoder_labeling_v3/full_training.log
```

- ברירת מחדל `--source db` (מהיר; טוען זוגות + טקסטים מ-SQLite). חלופות: `--source csv` (מ-`data/exports/training_pairs/*.csv`) או `--source json`.
- לוג: `tail -f models/bi_encoder_labeling_v3/full_training.log`

אופציונלי — פחות עומס לניסוי ביניים:
```bash
python3 scripts/train_bi_encoder.py --epochs 1 --batch-size 16 --max-train-pairs 10000
```

## אחרי האימון

```bash
# דיוק זוגות + מטריקות ב-training_metrics.json
cat models/bi_encoder_labeling_v3/training_metrics.json

# ציון ריקולים בודדים (שלב 7 — תצוגה מקדימה)
python3 scripts/score_alerts.py --split test
python3 scripts/score_alerts.py --split train --out data/bi_encoder_scores_train.json
```

## נתוני קלט (שלב 5)

- `data/synthetic_training_pairs.json` — מלא
- CSV: `data/exports/training_pairs/train_pairs.csv`, `test_pairs.csv`
- DB: `training_split_members`, `synthetic_training_pairs`

## מתודולוגיה (תזכורת)

- **Loss:** `BCE(σ(score_A - score_B), label)` — בקוד: `binary_cross_entropy_with_logits(score_A - score_B, label)`
- **label=1** ⟺ `composite_A > composite_B` (BT composite = ממוצע שווה ⅓×3 ממדים)
- Split ברמת **alert** (seed=42), לא זוגות צולבים train↔test

## צעדים הבאים (אחרי אימון מלא)

1. הערכה מול בייסליין (severity_raw, TF-IDF)
2. שלב 7 — threshold / top-K יומי ל-MOH
3. שלב 8 — counterfactuals

## תלויות

`requirements-ml.txt`: torch, transformers, accelerate
