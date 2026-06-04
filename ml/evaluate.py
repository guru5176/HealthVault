"""
evaluate.py — Evaluate the saved best model on the full test set.

Metrics reported:
  - CER  (Character Error Rate)   — primary OCR metric, lower = better
  - WER  (Word Error Rate)        — 0 = all words correct
  - Exact Match Accuracy          — % of images where prediction == ground truth exactly

Outputs:
  - Terminal summary table
  - results/eval_report.csv  (first 30 sample predictions for inspection)

Usage:
    python evaluate.py
"""

import os
import torch
import pandas as pd
from torch.utils.data import DataLoader
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from tqdm import tqdm
from jiwer import cer, wer

import config
from dataset import PrescriptionDataset


def main():
    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    best_path = os.path.join(config.CHECKPOINT_DIR, "best_model")

    # ── Load model ────────────────────────────────────────────────────────────
    # Try local checkpoint first, fall back to Hugging Face
    if os.path.isdir(best_path):
        print(f"[Evaluate] Loading best model from local checkpoint: {best_path}")
        model_id = best_path
    else:
        print(f"[Evaluate] No local checkpoint found. Loading base model from HF: {config.MODEL_NAME}")
        model_id = config.MODEL_NAME

    processor = TrOCRProcessor.from_pretrained(model_id)
    model     = VisionEncoderDecoderModel.from_pretrained(model_id).to(device)
    model.eval()

    # ── Test DataLoader ───────────────────────────────────────────────────────
    test_ds = PrescriptionDataset(
        config.TEST_LABEL_CSV, config.TEST_IMG_DIR, processor, is_train=False
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=config.NUM_WORKERS,
        pin_memory=config.PIN_MEMORY,
    )

    all_preds, all_labels = [], []

    # ── Inference ─────────────────────────────────────────────────────────────
    print(f"\n[Evaluate] Running inference on {len(test_ds)} test samples...")
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating"):
            pixel_values = batch["pixel_values"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=config.USE_FP16):
                generated_ids = model.generate(pixel_values)

            preds = processor.tokenizer.batch_decode(
                generated_ids.cpu(), skip_special_tokens=True
            )

            label_ids = batch["labels"].clone()
            label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
            labels = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

            all_preds.extend(preds)
            all_labels.extend(labels)

    # ── Metrics ───────────────────────────────────────────────────────────────
    total_cer   = cer(all_labels, all_preds)
    total_wer   = wer(all_labels, all_preds)
    exact_match = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)

    print(f"\n{'='*55}")
    print(f"  {'Metric':<30} {'Value':>10}")
    print(f"  {'-'*44}")
    print(f"  {'CER  (Character Error Rate)':<30} {total_cer*100:>9.2f}%")
    print(f"  {'WER  (Word Error Rate)':<30} {total_wer*100:>9.2f}%")
    print(f"  {'Exact Match Accuracy':<30} {exact_match*100:>9.2f}%")
    print(f"  {'Test Samples':<30} {len(all_labels):>10}")
    print(f"{'='*55}")

    # ── Save sample predictions ───────────────────────────────────────────────
    n   = min(30, len(all_labels))
    df  = pd.DataFrame({
        "filename"    : test_ds.samples["filename"].tolist()[:n],
        "ground_truth": all_labels[:n],
        "predicted"   : all_preds[:n],
        "correct"     : [p == l for p, l in zip(all_preds[:n], all_labels[:n])],
    })

    report_path = os.path.join(config.RESULTS_DIR, "eval_report.csv")
    df.to_csv(report_path, index=False)

    print(f"\n[Evaluate] Sample predictions (first {n}):")
    print(df.to_string(index=False))
    print(f"\n[Evaluate] Full report saved -> {report_path}")


if __name__ == "__main__":
    main()
