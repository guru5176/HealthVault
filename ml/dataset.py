"""
dataset.py — PyTorch Dataset for word-level handwritten prescription OCR.

CSV format (with header row 'Images', 'Text'):
    Column 0 : image filename   e.g. "P0001.jpg"
    Column 1 : ground truth     e.g. "Nexcital"   (Mixed Case drug names)

Performance strategy:
    ALL raw images (train + test) are loaded from disk ONCE at startup and
    stored as numpy arrays in CPU RAM (~400-600 MB total).
    During training, augmentation is applied to the in-memory numpy array
    — eliminating disk I/O per batch while keeping augmentation variety.
"""

import os
import pandas as pd
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
from torch.utils.data import Dataset
from transformers import TrOCRProcessor

import config
from augment import get_train_augmentation, apply_augmentation


class PrescriptionDataset(Dataset):
    """
    Maps CSV labels to image files and prepares (pixel_values, labels)
    tensors for the TrOCR VisionEncoderDecoderModel.

    Args:
        csv_path  : Full path to the .csv label file
        img_dir   : Directory containing the image files
        processor : HuggingFace TrOCRProcessor
        is_train  : If True, applies augmentation each call; test is always clean
    """

    def __init__(
        self,
        csv_path: str,
        img_dir: str,
        processor: TrOCRProcessor,
        is_train: bool = True,
    ):
        self.processor = processor
        self.is_train  = is_train
        self.augment   = get_train_augmentation() if is_train else None

        # ── Load CSV labels ──────────────────────────────────────────────────
        df = pd.read_csv(csv_path, header=0)
        df = df.iloc[:, [0, 1]]
        df.columns = ["filename", "label"]
        df["filename"] = df["filename"].astype(str).str.strip()
        df["label"]    = df["label"].astype(str).str.strip()

        # Drop rows with missing images
        before = len(df)
        df = df[
            df["filename"].apply(lambda f: os.path.exists(os.path.join(img_dir, f)))
        ].reset_index(drop=True)
        if len(df) != before:
            print(f"[Dataset] WARNING: {before - len(df)} image(s) missing — skipped.")

        self.samples = df
        split = "Train" if is_train else "Test"
        print(f"[Dataset] {split} set: {len(self.samples)} samples")

        # ── Pre-encode labels (done once — same every epoch) ─────────────────
        self.label_ids = []
        for label in df["label"].tolist():
            ids = processor.tokenizer(
                label,
                padding="max_length",
                max_length=config.MAX_LABEL_LEN,
                truncation=True,
                return_tensors="pt",
            ).input_ids.squeeze(0)
            ids[ids == processor.tokenizer.pad_token_id] = -100
            self.label_ids.append(ids)

        # ── Preload raw images as uint8 numpy arrays into RAM ─────────────────
        # This eliminates all disk I/O during training.
        # Augmentation is still applied at __getitem__ so it varies each epoch.
        print(f"[Dataset] Loading {len(df)} images into RAM...")
        self.raw_images = []
        for row in tqdm(df.itertuples(), total=len(df), desc=f"  {split} images"):
            img_path = os.path.join(img_dir, row.filename)
            img_np   = np.array(Image.open(img_path).convert("RGB"))  # uint8 HxWx3
            self.raw_images.append(img_np)

        ram_mb = sum(a.nbytes for a in self.raw_images) / 1e6
        print(f"[Dataset] RAM used for raw images: {ram_mb:.0f} MB\n")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        img_np    = self.raw_images[idx]        # uint8 numpy HxWx3
        label_ids = self.label_ids[idx]

        # Apply augmentation on train set (each call gives different result)
        if self.is_train and self.augment is not None:
            img_np = self.augment(image=img_np)["image"]

        # Convert numpy → PIL for TrOCRProcessor
        image        = Image.fromarray(img_np)
        pixel_values = self.processor(
            images=image, return_tensors="pt"
        ).pixel_values.squeeze(0)

        return {
            "pixel_values": pixel_values,   # FloatTensor [C, H, W]
            "labels":       label_ids,       # LongTensor  [seq_len]
        }
