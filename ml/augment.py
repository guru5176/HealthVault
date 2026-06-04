"""
augment.py — Albumentations augmentation pipeline for training images.

Designed specifically for handwritten medical prescription words:
  - Rotation          : Doctors rarely write perfectly horizontal
  - Perspective       : Phone camera angle variation
  - ElasticTransform  : Pen pressure & cursive stroke variation
  - GaussianBlur      : Photo blur / out-of-focus shots
  - GaussNoise        : Camera sensor noise in low-light photos
  - BrightnessContrast: Ambient lighting differences
"""

import numpy as np
import albumentations as A
from PIL import Image


def get_train_augmentation() -> A.Compose:
    """
    Returns the Albumentations Compose pipeline for training.
    Applied only during training — test images are left clean.
    """
    return A.Compose([
        # Slight rotation — handwriting is rarely perfectly straight
        A.Rotate(
            limit=7,
            border_mode=0,          # Fill empty pixels with black
            p=0.5
        ),

        # Mild perspective warp — simulates phone camera angle
        A.Perspective(
            scale=(0.02, 0.05),
            p=0.3
        ),

        # Elastic deformation — simulates cursive pen strokes & pressure
        A.ElasticTransform(
            alpha=30,
            sigma=5,
            p=0.3
        ),

        # Gaussian blur — simulates out-of-focus phone photos
        A.GaussianBlur(
            blur_limit=(3, 5),
            p=0.3
        ),

        # Gaussian noise — camera sensor noise
        A.GaussNoise(
            std_range=(0.02, 0.08),   # albumentations 2.x uses std_range not var_limit
            p=0.3
        ),

        # Brightness & contrast — varying lighting conditions
        A.RandomBrightnessContrast(
            brightness_limit=0.2,
            contrast_limit=0.2,
            p=0.5
        ),
    ])


def apply_augmentation(pil_image: Image.Image, augment_fn: A.Compose) -> Image.Image:
    """
    Applies an Albumentations pipeline to a PIL image.

    Flow: PIL → numpy (HxWxC uint8) → augment → PIL
    The TrOCRProcessor downstream expects a PIL image.

    Args:
        pil_image   : Input PIL image (will be converted to RGB internally)
        augment_fn  : Albumentations Compose pipeline from get_train_augmentation()

    Returns:
        Augmented PIL image in RGB mode
    """
    img_np    = np.array(pil_image.convert("RGB"))        # → uint8 HxWx3
    augmented = augment_fn(image=img_np)["image"]         # → uint8 HxWx3
    return Image.fromarray(augmented)                     # → PIL RGB
