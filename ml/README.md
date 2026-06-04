# HealthVault — Prescription OCR (ML Module)

Fine-tuned **TrOCR** model for reading word-level handwritten drug names from prescription images.

---

## Setup

### Step 1 — Install PyTorch (CUDA 12.1 for RTX 4060)

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 2 — Install remaining dependencies

```bash
cd ml/
pip install -r requirements.txt
```

### Step 3 — Verify CUDA is available

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Expected: True  NVIDIA GeForce RTX 4060 Laptop GPU
```

---

## Data Layout

Your data paths are configured in `config.py`. No files need to be moved.

```
D:/hv/RxHandBD-ML/
├── Train_Set/          ← 4,464 training images (P0001.jpg …)
├── Test_Set/           ← 1,116 test images
├── Train_Label.xlsx    ← Col A: filename, Col B: drug name
└── Test_Label.xlsx
```

Excel format (no header row):

| Column A   | Column B  |
|------------|-----------|
| P0001.jpg  | Nexcital  |
| P0002.jpg  | Inderen   |

---

## Scripts

| Script         | Purpose                                      | Command                                     |
|----------------|----------------------------------------------|---------------------------------------------|
| `train.py`     | Fine-tune TrOCR, save best model             | `python train.py`                           |
| `evaluate.py`  | CER / WER / Exact Match on test set          | `python evaluate.py`                        |
| `predict.py`   | Predict one image (sanity check)             | `python predict.py --image P0001.jpg --dir D:/hv/RxHandBD-ML/Test_Set` |

---

## Training Details

| Setting             | Value                                  |
|---------------------|----------------------------------------|
| Base model          | `microsoft/trocr-base-handwritten`     |
| Batch size          | 32                                     |
| Learning rate       | 5e-5                                   |
| Max epochs          | 25 (early stopping after 5 stale)      |
| Mixed precision     | fp16 (RTX 4060 optimised)              |
| Augmentation        | Rotation, ElasticTransform, Noise, Blur, Perspective |

Checkpoints are saved to `checkpoints/best_model/`.

---

## Expected Results (RTX 4060)

| Metric              | Target      |
|---------------------|-------------|
| CER                 | < 15%       |
| Exact Match         | > 75%       |
| Training time       | ~30–60 min  |

---

## Output Files

| File                          | Description                        |
|-------------------------------|------------------------------------|
| `checkpoints/best_model/`     | Saved model weights & processor    |
| `results/eval_report.csv`     | 30 sample prediction comparisons   |
