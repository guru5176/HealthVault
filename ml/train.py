"""
train.py — Fine-tune microsoft/trocr-base-handwritten on the prescription dataset.

Features:
  - Mixed precision (fp16) for RTX 4060
  - OneCycleLR scheduler with warmup
  - Gradient clipping
  - Per-epoch CER evaluation on test set
  - Best model auto-saved to checkpoints/best_model/
  - Early stopping based on CER

Usage:
    python train.py
"""

import os
import random
import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from tqdm import tqdm
from jiwer import cer

import config
from dataset import PrescriptionDataset


# ─── Reproducibility ─────────────────────────────────────────────────────────
def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# ─── Evaluation ──────────────────────────────────────────────────────────────
def evaluate_cer(model, loader, processor, device) -> float:
    """
    Run inference on a DataLoader and return the Character Error Rate (CER).
    Lower is better. CER = 0.0 means perfect prediction.
    """
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch in tqdm(loader, desc="  Evaluating", leave=False):
            pixel_values = batch["pixel_values"].to(device)

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=config.USE_FP16):
                generated_ids = model.generate(pixel_values)

            # Decode predictions
            preds = processor.tokenizer.batch_decode(
                generated_ids.cpu(), skip_special_tokens=True
            )

            # Decode ground truth (undo the -100 masking applied in dataset.py)
            label_ids = batch["labels"].clone()
            label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
            labels = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)

            all_preds.extend(preds)
            all_labels.extend(labels)

    model.train()
    return cer(all_labels, all_preds)


# ─── Main Training Loop ───────────────────────────────────────────────────────
def main():
    set_seed(config.SEED)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Train] Device : {device}")
    if device.type == "cuda":
        print(f"[Train] GPU    : {torch.cuda.get_device_name(0)}")
        print(f"[Train] VRAM   : {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"[Train] fp16   : {config.USE_FP16}")

    # ── Load pre-trained TrOCR ────────────────────────────────────────────────
    print(f"\n[Train] Loading model: {config.MODEL_NAME}")
    processor = TrOCRProcessor.from_pretrained(config.MODEL_NAME)
    model     = VisionEncoderDecoderModel.from_pretrained(config.MODEL_NAME)

    # Required token configuration for seq2seq generation
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id           = processor.tokenizer.pad_token_id
    model.config.vocab_size             = model.config.decoder.vocab_size

    model = model.to(device)

    # ── Datasets & DataLoaders ────────────────────────────────────────────────
    print("\n[Train] Building datasets...")
    train_ds = PrescriptionDataset(
        config.TRAIN_LABEL_CSV, config.TRAIN_IMG_DIR, processor, is_train=True
    )
    test_ds = PrescriptionDataset(
        config.TEST_LABEL_CSV, config.TEST_IMG_DIR, processor, is_train=False
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=config.NUM_WORKERS,
        pin_memory=config.PIN_MEMORY,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=config.NUM_WORKERS,
        pin_memory=config.PIN_MEMORY,
    )

    # ── Optimiser & Scheduler ─────────────────────────────────────────────────
    optimizer = AdamW(
        model.parameters(),
        lr=config.LEARNING_RATE,
        weight_decay=config.WEIGHT_DECAY,
    )
    scheduler = OneCycleLR(
        optimizer,
        max_lr=config.LEARNING_RATE,
        steps_per_epoch=len(train_loader),
        epochs=config.NUM_EPOCHS,
        pct_start=config.WARMUP_RATIO,
    )
    scaler = torch.amp.GradScaler(enabled=config.USE_FP16)

    # ── Training ──────────────────────────────────────────────────────────────
    best_cer     = float("inf")
    patience_ctr = 0
    best_path    = os.path.join(config.CHECKPOINT_DIR, "best_model")

    print(f"\n[Train] Starting training for up to {config.NUM_EPOCHS} epochs...")
    print(f"[Train] Early stopping patience: {config.EARLY_STOP_PATIENCE}\n")

    for epoch in range(1, config.NUM_EPOCHS + 1):
        model.train()
        epoch_loss = 0.0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch:02d}/{config.NUM_EPOCHS}")
        for batch in pbar:
            pixel_values = batch["pixel_values"].to(device)
            labels       = batch["labels"].to(device)

            optimizer.zero_grad()

            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=config.USE_FP16):
                outputs = model(pixel_values=pixel_values, labels=labels)
                loss    = outputs.loss

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            epoch_loss += loss.item()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        avg_loss = epoch_loss / len(train_loader)

        # ── CER evaluation every EVAL_EVERY epochs ────────────────────────────
        if epoch % config.EVAL_EVERY == 0 or epoch == config.NUM_EPOCHS:
            val_cer = evaluate_cer(model, test_loader, processor, device)
            print(f"\n  -> Epoch {epoch:02d} | Avg Loss: {avg_loss:.4f} | Test CER: {val_cer:.4f} ({val_cer*100:.2f}%)")

            if val_cer < best_cer:
                best_cer     = val_cer
                patience_ctr = 0
                model.save_pretrained(best_path)
                processor.save_pretrained(best_path)
                print(f"  [OK] New best model saved -> CER: {best_cer:.4f}\n")
            else:
                patience_ctr += 1
                print(f"  [X] No improvement. Patience: {patience_ctr}/{config.EARLY_STOP_PATIENCE}\n")
                if patience_ctr >= config.EARLY_STOP_PATIENCE:
                    print(f"[Train] Early stopping triggered at epoch {epoch}.")
                    break
        else:
            print(f"  -> Epoch {epoch:02d} | Avg Loss: {avg_loss:.4f} | (eval skipped, runs every {config.EVAL_EVERY} epochs)")

    print(f"\n[Train] [DONE] Training complete.")
    print(f"[Train] Best CER : {best_cer:.4f} ({best_cer*100:.2f}%)")
    print(f"[Train] Model    : {best_path}")


if __name__ == "__main__":
    main()
