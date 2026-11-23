"""Semantic Document Chunker for RAG.
Splits extracted document texts while preserving page numbers, section headers, and metadata.
"""

from typing import List, Dict, Any
from app.models import DocumentChunk
from app.config import settings

class SemanticChunker:
    """Chunks documents while preserving context, page citations, and tabular structures."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_page_text(
        self,
        text: str,
        doc_id: str,
        doc_name: str,
        page_number: int,
        metadata: Dict[str, Any] = None,
        is_ocr: bool = False
    ) -> List[DocumentChunk]:
        """Chunks a single page's text into overlapping semantic segments."""
        if not text or not text.strip():
            return []

        chunks: List[DocumentChunk] = []
        paragraphs = text.split("\n\n")
        
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            words = para.split()
            para_len = len(words)

            if current_length + para_len > self.chunk_size and current_chunk:
                # Flush current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(DocumentChunk(
                    doc_id=doc_id,
                    doc_name=doc_name,
                    page_number=page_number,
                    content=chunk_text,
                    metadata=metadata or {},
                    is_ocr=is_ocr
                ))
                # Keep overlap if possible
                overlap_words = words[-min(self.overlap, len(words)):]
                current_chunk = [" ".join(overlap_words)] if overlap_words else []
                current_length = len(overlap_words)

            current_chunk.append(para)
            current_length += para_len

        # Flush remaining
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(DocumentChunk(
                doc_id=doc_id,
                doc_name=doc_name,
                page_number=page_number,
                content=chunk_text,
                metadata=metadata or {},
                is_ocr=is_ocr
            ))

        return chunks


chunker = SemanticChunker()
