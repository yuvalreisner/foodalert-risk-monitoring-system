#!/bin/bash
# Creates a clean handover zip for the Ministry of Health.
# Run from the project root: bash handover/pack_handover.sh

set -e
DEST="foodsafe_intelligence"
ZIP="${DEST}.zip"

echo "=== FoodSafe Intelligence — Building handover package ==="

rm -rf "$DEST"
mkdir -p "$DEST/scripts"
mkdir -p "$DEST/src/collectors"
mkdir -p "$DEST/models/bi_encoder_labeling_v3"
mkdir -p "$DEST/data"
mkdir -p "$DEST/reports"

# Documentation
echo "Copying documentation..."
cp handover/README_HE.md   "$DEST/README_HE.md"
cp handover/INSTALL.md     "$DEST/INSTALL.md"
cp requirements.txt        "$DEST/requirements.txt"

# Operational scripts only (not training/labeling scripts)
echo "Copying scripts..."
cp scripts/ingest.py              "$DEST/scripts/"
cp scripts/score_all_alerts.py    "$DEST/scripts/"
cp scripts/generate_dashboard.py  "$DEST/scripts/"
cp scripts/rank_daily.py          "$DEST/scripts/"
cp scripts/counterfactuals.py     "$DEST/scripts/"

# Source library
echo "Copying src/..."
cp src/__init__.py   "$DEST/src/"
cp src/db.py         "$DEST/src/"
cp src/dedup.py      "$DEST/src/"
cp src/pipeline.py   "$DEST/src/"
cp src/schema.sql    "$DEST/src/"
cp src/collectors/__init__.py    "$DEST/src/collectors/"
cp src/collectors/base.py        "$DEST/src/collectors/"
cp src/collectors/fda_enforcement.py "$DEST/src/collectors/"
cp src/collectors/fsis.py        "$DEST/src/collectors/"
cp src/collectors/fsa_uk.py      "$DEST/src/collectors/"
cp src/collectors/rasff.py       "$DEST/src/collectors/"

# Trained model
echo "Copying model (314MB — may take a moment)..."
cp models/bi_encoder_labeling_v3/best_model.pt \
   "$DEST/models/bi_encoder_labeling_v3/"
cp models/bi_encoder_labeling_v3/training_metrics.json \
   "$DEST/models/bi_encoder_labeling_v3/"
cp -r models/bi_encoder_labeling_v3/encoder \
   "$DEST/models/bi_encoder_labeling_v3/"

# Database
echo "Copying database (alerts.db)..."
cp data/alerts.db "$DEST/data/"

# Zip
echo "Creating $ZIP..."
zip -r "$ZIP" "$DEST" -x "*.pyc" -x "*/__pycache__/*"
rm -rf "$DEST"

SIZE=$(du -sh "$ZIP" | cut -f1)
echo ""
echo "=== Done ==="
echo "Package: $ZIP  ($SIZE)"
echo ""
echo "Send this file to the Ministry of Health IT team."
echo "They should follow README_HE.md inside the zip."
