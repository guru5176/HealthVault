import os
import sys
import json
import warnings
import logging

# Suppress warnings and standard logs so stdout stays clean for JSON parsing in Node.js
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)

# Redirect standard output to stderr temporarily while importing and loading
original_stdout = sys.stdout
sys.stdout = sys.stderr

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Restore stdout
sys.stdout = original_stdout

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided."}))
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    if not os.path.isfile(image_path):
        print(json.dumps({"error": f"File not found: {image_path}"}))
        sys.exit(1)
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Path is relative to the ml/ directory, but this script might be run from backend/
    # Let's resolve the path robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    best_path = os.path.join(script_dir, "checkpoints", "best_model")
    
    if not os.path.isdir(best_path):
        print(json.dumps({"error": f"Model not found at {best_path}"}))
        sys.exit(1)
        
    try:
        # Load model and processor (redirecting prints to stderr)
        sys.stdout = sys.stderr
        processor = TrOCRProcessor.from_pretrained(best_path, use_fast=True)
        model = VisionEncoderDecoderModel.from_pretrained(best_path).to(device)
        model.eval()
        sys.stdout = original_stdout
        
        # Load and predict
        image = Image.open(image_path).convert("RGB")
        pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
        
        with torch.no_grad():
            with torch.autocast(device_type="cuda" if "cuda" in str(device) else "cpu", dtype=torch.float16, enabled=torch.cuda.is_available()):
                generated_ids = model.generate(pixel_values, max_new_tokens=32)
                
        result = processor.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        
        print(json.dumps({"prediction": result}))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
