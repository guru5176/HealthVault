import torch
from transformers import pipeline
from PIL import Image
import os

# Load model from Hugging Face
model_id = "microsoft/trocr-base-handwritten"
print(f"Loading {model_id} from Hugging Face...")
device = 0 if torch.cuda.is_available() else -1
ocr_pipeline = pipeline("image-to-text", model=model_id, device=device)

# Path to a test image
img_dir = "../data set/RxHandBD-ML/Test_Set"
img_name = "P0001.jpg"
img_path = os.path.join(img_dir, img_name)

if os.path.exists(img_path):
    print(f"Processing {img_path}...")
    image = Image.open(img_path).convert("RGB")
    result = ocr_pipeline(image)
    print(f"\nResult: {result}")
else:
    print(f"Image not found at {img_path}")
