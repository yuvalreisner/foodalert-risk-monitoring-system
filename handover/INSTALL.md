# FoodSafe Intelligence — Technical Installation Guide

## System Requirements

- Python 3.9 or higher
- 4GB RAM minimum (8GB recommended for model scoring)
- 2GB free disk space
- Internet connection (for data collection)

## Step 1 — Install Python

Download from https://www.python.org/downloads/ (version 3.9+).  
During installation on Windows: check **"Add Python to PATH"**.

Verify:
```bash
python3 --version
# Expected: Python 3.9.x or higher
```

## Step 2 — Install dependencies

```bash
cd foodsafe_intelligence
pip3 install -r requirements.txt
```

This installs: PyTorch, Transformers (HuggingFace), Requests, NumPy, tqdm.

**Note on PyTorch:** If the machine has no GPU, PyTorch will run on CPU — scoring ~23,000 alerts takes ~15 minutes. With GPU (CUDA/MPS) it takes ~2 minutes.

## Step 3 — Verify installation

```bash
python3 -c "import torch; import transformers; print('OK')"
# Expected: OK
```

## Step 4 — Verify model files

```bash
ls models/bi_encoder_labeling_v3/
# Expected: best_model.pt  encoder/  training_metrics.json
```

If `best_model.pt` is missing (>300MB files are sometimes stripped from archives), contact the development team.

## Step 5 — Test run

```bash
python3 scripts/generate_dashboard.py --window 30 --out reports/test
open reports/test.html   # Mac
start reports/test.html  # Windows
```

If the dashboard opens correctly — installation is complete.

## Troubleshooting

| Error | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'torch'` | Run `pip3 install -r requirements.txt` |
| `No such file: best_model.pt` | Model file missing — re-download handover package |
| `sqlite3.OperationalError` | Run `python3 scripts/score_all_alerts.py` first |
| Slow scoring (~1hr) | Normal on CPU — consider a machine with GPU |
