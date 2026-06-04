"""
config.py — Central configuration for the HealthVault Prescription OCR model.
All paths, hyperparameters, and flags are defined here.
Edit this file to tune the training run.
"""

import os

# ─── Base paths ───────────────────────────────────────────────────────────────
# ml/ folder (this file's location)
_ML_DIR      = os.path.dirname(os.path.abspath(__file__))
# Project root  (one level up from ml/)
_PROJECT_DIR = os.path.dirname(_ML_DIR)
# Dataset root
_DATA_DIR    = os.path.join(_PROJECT_DIR, "data set", "RxHandBD-ML")

# ─── Data Paths ───────────────────────────────────────────────────────────────
# Actual layout on disk:
#   new_project/data set/RxHandBD-ML/Train_Set/   ← 4,464 training images
#   new_project/data set/RxHandBD-ML/Test_Set/    ← 1,116 test images
#   new_project/data set/RxHandBD-ML/Train_Label.csv
#   new_project/data set/RxHandBD-ML/Test_Label.csv
TRAIN_IMG_DIR  = os.path.join(_DATA_DIR, "Train_Set")
TEST_IMG_DIR   = os.path.join(_DATA_DIR, "Test_Set")
TRAIN_LABEL_CSV = os.path.join(_DATA_DIR, "Train_Label.csv")
TEST_LABEL_CSV  = os.path.join(_DATA_DIR, "Test_Label.csv")

# ─── Output Paths ─────────────────────────────────────────────────────────────
CHECKPOINT_DIR = "checkpoints"   # Best model weights saved here
RESULTS_DIR    = "results"       # Eval reports saved here

# ─── Model ────────────────────────────────────────────────────────────────────
MODEL_NAME = "microsoft/trocr-base-handwritten"
# MODEL_NAME = "shubham879/trocr-prescription"

# ─── Training Hyperparameters ─────────────────────────────────────────────────
BATCH_SIZE    = 32        # Safe for RTX 4060 (8GB VRAM) with fp16
LEARNING_RATE = 5e-5      # AdamW default for fine-tuning Transformers
NUM_EPOCHS    = 25        # Max epochs (early stopping may cut this short)
WEIGHT_DECAY  = 0.01      # AdamW regularisation
WARMUP_RATIO  = 0.1       # 10% of total steps used for LR warmup

# ─── Early Stopping ───────────────────────────────────────────────────────────
EARLY_STOP_PATIENCE = 5   # Stop if CER doesn't improve for N consecutive evals
EVAL_EVERY          = 2   # Evaluate on test set every N epochs (saves time)

# ─── DataLoader ───────────────────────────────────────────────────────────────
# NOTE: On Windows, NUM_WORKERS > 0 causes huge multiprocessing overhead.
# Keep at 0 for Windows. Linux/WSL users can set to 4.
NUM_WORKERS = 0
PIN_MEMORY  = False   # pin_memory only benefits when NUM_WORKERS > 0

# ─── Mixed Precision ──────────────────────────────────────────────────────────
USE_FP16 = True            # Enable fp16 for RTX 4060 — ~2x speedup with no accuracy loss

# ─── Label / Tokeniser ────────────────────────────────────────────────────────
MAX_LABEL_LEN = 32         # Max token length for a drug name (well within this limit)

# ─── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42

# ─── Auto-create output directories ───────────────────────────────────────────
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
