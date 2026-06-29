from backend.services.ocr_service import ocr_service
with open("dummy.png", "rb") as f:
    text = ocr_service.extract_text(f.read())
print("Extracted:", text)
