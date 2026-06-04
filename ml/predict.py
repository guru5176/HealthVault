"""
predict.py — Single-image inference for sanity checking the trained model.

Usage:
    python predict.py --image P0001.jpg --dir D:/hv/RxHandBD-ML/Test_Set
    python predict.py --image D:/hv/RxHandBD-ML/Test_Set/P0001.jpg
"""

import os
import argparse
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

import config


def load_model(model_path: str, device: torch.device):
    """Load the saved processor and model from a checkpoint directory."""
    processor = TrOCRProcessor.from_pretrained(model_path)
    model     = VisionEncoderDecoderModel.from_pretrained(model_path).to(device)
    model.eval()
    return processor, model


def predict_image(image_path: str, processor, model, device: torch.device) -> str:
    """
    Run inference on a single image and return the predicted text.

    Args:
        image_path : Full path to the image file
        processor  : TrOCRProcessor
        model      : Fine-tuned VisionEncoderDecoderModel
        device     : torch.device

    Returns:
        Predicted string (e.g., "Nexcital")
    """
    image        = Image.open(image_path).convert("RGB")
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=config.USE_FP16):
            generated_ids = model.generate(pixel_values)

    return processor.tokenizer.decode(generated_ids[0], skip_special_tokens=True)


def main():
    parser = argparse.ArgumentParser(
        description="Predict handwritten drug name from a single prescription image."
    )
    parser.add_argument(
        "--image", required=True,
        help="Image filename (e.g. P0001.jpg) or full path to the image."
    )
    parser.add_argument(
        "--dir", default=None,
        help="Optional base directory. If set, image is joined with this dir."
    )
    args = parser.parse_args()

    # ── Resolve image path ────────────────────────────────────────────────────
    img_path = os.path.join(args.dir, args.image) if args.dir else args.image
    if not os.path.isfile(img_path):
        print(f"[Error] Image not found: {img_path}")
        return

    # ── Load model ────────────────────────────────────────────────────────────
    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    best_path = os.path.join(config.CHECKPOINT_DIR, "best_model")

    if os.path.isdir(best_path):
        model_id = best_path
        print(f"[Predict] Loading fine-tuned model from: {model_id}")
    else:
        model_id = config.MODEL_NAME
        print(f"[Predict] No fine-tuned model found. Loading base model: {model_id}")

    print(f"[Predict] Input image        : {img_path}")
    processor, model = load_model(model_id, device)

    # ── Predict ───────────────────────────────────────────────────────────────
    result = predict_image(img_path, processor, model, device)
    print(f"\n  -> Predicted text: \"{result}\"\n")


if __name__ == "__main__":
    main()
