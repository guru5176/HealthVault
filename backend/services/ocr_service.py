import os
import logging
import tempfile
from paddleocr import PaddleOCR

logger = logging.getLogger("health_wallet.ocr")


class OCRService:
    def __init__(self):
        self.ocr = None

    def _get_ocr(self) -> PaddleOCR:
        if self.ocr is None:
            logger.info("Initializing PaddleOCR...")
            self.ocr = PaddleOCR(enable_mkldnn=False)
            logger.info("PaddleOCR initialized successfully.")
        return self.ocr

    def extract_text(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes using PaddleOCR for both detection and recognition."""
        ocr = self._get_ocr()

        # Write bytes to a temporary file because PaddleOCR works best with file paths
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_bytes)
            temp_file_path = temp_file.name

        try:
            logger.info(f"Running PaddleOCR on temporary file: {temp_file_path}")

            result = ocr.predict(temp_file_path)

            rec_texts = []
            for res in result:
                # Support both key names for compatibility across PaddleOCR versions
                if "rec_texts" in res:
                    rec_texts.extend(res["rec_texts"])
                elif "text" in res:
                    rec_texts.append(res["text"])

            extracted = "\n".join(rec_texts)
            logger.info(f"PaddleOCR extracted {len(rec_texts)} text regions.")
            return extracted

        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}", exc_info=True)
            return ""
        finally:
            # Clean up the temporary file
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")


ocr_service = OCRService()
