
"""PDF extraction using PDFium with pypdf fallback.

Preserves page references, uses genuine Tesseract OCR for scanned
pages, and never indexes fabricated text when extraction fails.
"""

import io
import os
import time
import uuid
import logging
from typing import Tuple, List

from app.models import DocumentMetadata, DocumentChunk
from app.document_processor.sanitizer import sanitizer
from app.document_processor.ocr_service import ocr_service
from app.document_processor.chunker import chunker

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and metadata from uploaded PDF documents."""

    @classmethod
    def extract_document(
        cls,
        file_path: str,
        original_filename: str
    ) -> Tuple[DocumentMetadata, List[DocumentChunk]]:

        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                "The uploaded PDF file was not found."
            )

        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        file_size = os.path.getsize(file_path)

        all_chunks: List[DocumentChunk] = []
        unreadable_pages: List[int] = []
        security_reasons: List[str] = []

        tables_count = 0
        total_pages = 0
        has_scanned = False
        security_flagged = False

        def process_page_text(
            text: str,
            page_number: int,
            is_ocr: bool
        ) -> None:
            nonlocal security_flagged

            if not text or not text.strip():
                unreadable_pages.append(page_number)
                return

            clean_text, flagged, detected_patterns = (
                sanitizer.sanitize_text(text)
            )

            if flagged:
                security_flagged = True
                security_reasons.extend(detected_patterns)

            page_chunks = chunker.chunk_page_text(
                text=clean_text,
                doc_id=doc_id,
                doc_name=original_filename,
                page_number=page_number,
                metadata={"total_pages": total_pages},
                is_ocr=is_ocr
            )

            all_chunks.extend(page_chunks)

        # Check encryption before attempting extraction.
        try:
            import pypdf

            reader = pypdf.PdfReader(file_path)

            if reader.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

        except ValueError:
            raise

        except Exception as exc:
            logger.warning(
                "Initial PDF validation could not complete: %s",
                type(exc).__name__
            )

        # Primary extraction: PDFium.
        try:
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(file_path)

            try:
                total_pages = len(doc)

                for page_index in range(total_pages):
                    page_number = page_index + 1
                    page = doc[page_index]

                    text = ""
                    page_used_ocr = False

                    # Extract digitally embedded text.
                    try:
                        text_page = page.get_textpage()
                        text = (
                            text_page.get_text_range() or ""
                        ).strip()

                        text_page.close()

                    except Exception:
                        logger.warning(
                            "Digital text extraction failed "
                            "for page %s",
                            page_number
                        )

                    # Detect pages that need OCR.
                    if ocr_service.is_page_scanned(
                        text,
                        image_count=1
                    ):
                        has_scanned = True

                        try:
                            bitmap = page.render(scale=2)
                            image = bitmap.to_pil()

                            image_buffer = io.BytesIO()
                            image.save(
                                image_buffer,
                                format="PNG"
                            )

                            ocr_text, success, confidence = (
                                ocr_service.perform_ocr_on_page(
                                    image_buffer.getvalue(),
                                    page_number
                                )
                            )

                            if success and ocr_text.strip():
                                text = ocr_text
                                page_used_ocr = True

                                logger.info(
                                    "OCR completed for page %s "
                                    "with confidence %.3f",
                                    page_number,
                                    confidence
                                )
                            else:
                                logger.warning(
                                    "OCR could not read page %s",
                                    page_number
                                )
                                text = ""

                        except Exception:
                            logger.exception(
                                "PDFium rendering or OCR failed "
                                "for page %s",
                                page_number
                            )
                            text = ""

                    # Basic table indicator.
                    if (
                        "\t" in text
                        or "|" in text
                        or "  " in text
                    ):
                        tables_count += 1

                    process_page_text(
                        text=text,
                        page_number=page_number,
                        is_ocr=page_used_ocr
                    )

            finally:
                doc.close()

        except ValueError:
            raise

        except Exception as pdfium_error:
            logger.warning(
                "PDFium extraction failed; trying pypdf "
                "text fallback: %s",
                type(pdfium_error).__name__
            )

            # Reset partial extraction to prevent duplicate chunks.
            all_chunks = []
            unreadable_pages = []
            security_reasons = []

            tables_count = 0
            total_pages = 0
            has_scanned = False
            security_flagged = False

            try:
                import pypdf

                reader = pypdf.PdfReader(file_path)

                if reader.is_encrypted:
                    raise ValueError(
                        "Password-protected PDFs are not supported."
                    )

                total_pages = len(reader.pages)

                for page_index, page in enumerate(reader.pages):
                    page_number = page_index + 1
                    text = page.extract_text() or ""

                    # pypdf cannot render scanned pages.
                    # Do not create fake OCR text.
                    if not text.strip():
                        has_scanned = True

                    process_page_text(
                        text=text,
                        page_number=page_number,
                        is_ocr=False
                    )

            except ValueError:
                raise

            except Exception as fallback_error:
                logger.exception(
                    "PDF fallback extraction failed"
                )

                raise ValueError(
                    "The PDF could not be processed. "
                    "It may be corrupted, encrypted, or unsupported."
                ) from fallback_error

        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=original_filename,
            total_pages=total_pages,
            file_size_bytes=file_size,
            upload_timestamp=time.time(),
            is_scanned=has_scanned,
            unreadable_pages=unreadable_pages,
            detected_tables=tables_count,
            chunks_count=len(all_chunks),
            security_flagged=security_flagged,
            security_notes=(
                "Detected injection patterns: "
                + ", ".join(set(security_reasons))
                if security_flagged
                else None
            )
        )

        return metadata, all_chunks


pdf_extractor = PDFExtractor()
