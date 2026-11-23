
"""Real OCR service for scanned PDF pages.

Uses Tesseract through pytesseract. Never fabricates OCR output:
if OCR is unavailable or fails, the page is reported as unreadable.
"""

import io
import logging
import os
import pytesseract
from typing import Tuple

logger = logging.getLogger(__name__)

# Configure Tesseract executable
pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


class OCRService:
    """Detects scanned pages and extracts text using Tesseract OCR."""

    @staticmethod
    def is_page_scanned(extracted_text: str, image_count: int = 0) -> bool:
        """Identify pages that probably require OCR."""
        clean = (extracted_text or "").strip()

        if not clean:
            return True

        if len(clean) < 15 and image_count > 0:
            return True

        return False

    @staticmethod
    def perform_ocr_on_page(
        page_bytes: bytes,
        page_number: int
    ) -> Tuple[str, bool, float]:
        """Extract genuine text from a rendered PDF page.

        Returns:
            (extracted_text, success, confidence)

        Confidence is the average Tesseract word confidence,
        normalized to a value between 0.0 and 1.0.

        An unavailable OCR engine or failed extraction returns:
            ("", False, 0.0)
        """
        if not page_bytes:
            logger.warning("OCR skipped for page %s: empty image data", page_number)
            return "", False, 0.0

        try:
            import pytesseract
            from PIL import Image, ImageOps

            # Optional Windows configuration:
            # Set TESSERACT_CMD to the full path of tesseract.exe.
            pytesseract.pytesseract.tesseract_cmd = os.getenv(
                "TESSERACT_CMD",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

            language = os.getenv("TESSERACT_LANG", "eng")

            with Image.open(io.BytesIO(page_bytes)) as source:
                image = source.convert("RGB")
                image = ImageOps.grayscale(image)
                image = ImageOps.autocontrast(image)

                # Extract recognized words and their confidence values.
                data = pytesseract.image_to_data(
                    image,
                    lang=language,
                    config="--oem 3 --psm 6",
                    output_type=pytesseract.Output.DICT
                )

            words = []
            confidence_values = []

            for index, word in enumerate(data.get("text", [])):
                word = word.strip()

                if not word:
                    continue

                words.append(word)

                try:
                    confidence = float(data["conf"][index])
                    if confidence >= 0:
                        confidence_values.append(confidence)
                except (ValueError, TypeError, IndexError):
                    continue

            extracted_text = " ".join(words).strip()

            if not extracted_text:
                logger.warning(
                    "OCR returned no readable text for page %s",
                    page_number
                )
                return "", False, 0.0

            confidence = (
                sum(confidence_values) / len(confidence_values) / 100.0
                if confidence_values
                else 0.0
            )

            return extracted_text, True, round(confidence, 3)

        except ImportError:
            logger.exception(
                "OCR dependencies are unavailable for page %s",
                page_number
            )
            return "", False, 0.0

        except Exception:
            logger.exception(
                "OCR failed for PDF page %s",
                page_number
            )
            return "", False, 0.0


ocr_service = OCRService()
