
"""RAG retrieval engine for EXAMFLOW AI.

Provides owner-scoped semantic/lexical search, page retrieval,
question-number comparison, untrusted-content boundaries, and citations.
"""

import re
from typing import Any, Dict, List, Optional

from app.models import DocumentCitation
from app.retrieval.vector_store import vector_store
from app.document_processor.sanitizer import sanitizer


class RAGEngine:
    """Manages document retrieval, comparison, and source grounding."""

    @staticmethod
    def _format_chunk(chunk, score: Optional[float] = None) -> Dict[str, Any]:
        raw_content = chunk.content or ""

        wrapped_content = sanitizer.wrap_untrusted_content(
            raw_content,
            chunk.doc_name,
            chunk.page_number,
        )

        result = {
            "doc_id": chunk.doc_id,
            "doc_name": chunk.doc_name,
            "page_number": chunk.page_number,
            "raw_content": raw_content,
            "content": wrapped_content,
            "is_ocr": chunk.is_ocr,
        }

        if score is not None:
            result["relevance_score"] = score

        return result

    @staticmethod
    def search_documents(
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 4,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            return []

        results = vector_store.search(
            query=query,
            doc_ids=doc_ids,
            top_k=top_k,
            owner_id=owner_id,
            session_id=session_id,
        )

        return [
            RAGEngine._format_chunk(chunk, score)
            for chunk, score in results
        ]

    @staticmethod
    def retrieve_document_chunks(
        doc_id: str,
        page_numbers: List[int],
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not isinstance(doc_id, str) or not doc_id.strip():
            return []

        if not isinstance(page_numbers, list) or not page_numbers:
            return []

        chunks = vector_store.get_chunks_by_pages(
            doc_id,
            page_numbers,
            owner_id=owner_id,
            session_id=session_id,
        )

        return [
            RAGEngine._format_chunk(chunk)
            for chunk in chunks
        ]

    @staticmethod
    def get_document_chunks(
        doc_id: str,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        chunks = vector_store.get_document_chunks(
            doc_id,
            owner_id=owner_id,
            session_id=session_id,
        )

        return [
            RAGEngine._format_chunk(chunk)
            for chunk in chunks
        ]

    @staticmethod
    def _normalize_question_number(value: str):
        """Use integers for purely numeric IDs and strings for alphanumeric IDs."""
        return int(value) if value.isdigit() else value.upper()

    @staticmethod
    def _question_sort_key(value):
        match = re.match(r"^(\d+)(.*)$", str(value))

        if match:
            suffix = match.group(2)
            return int(match.group(1)), suffix

        return float("inf"), str(value)

    @staticmethod
    def _extract_question_map(chunks) -> Dict[Any, List[Dict[str, Any]]]:
        """Group source chunks by explicit question number."""

        question_map: Dict[Any, List[Dict[str, Any]]] = {}

        pattern = re.compile(
            r"\b(?:question|q)\s*[-#:]?\s*(\d+[A-Za-z]?)\b",
            re.IGNORECASE,
        )

        for chunk in chunks:
            matches = pattern.findall(chunk.content or "")

            for raw_number in set(matches):
                question_number = RAGEngine._normalize_question_number(
                    raw_number
                )

                question_map.setdefault(question_number, []).append({
                    "page_number": chunk.page_number,
                    "doc_name": chunk.doc_name,
                    "content": chunk.content or "",
                    "is_ocr": chunk.is_ocr,
                })

        return question_map

    @staticmethod
    def _text_matches(items_1, items_2) -> bool:
        """Check whether the extracted source text is identical."""

        normalize = lambda text: " ".join(
            str(text or "").casefold().split()
        )

        text_1 = {
            normalize(item["content"])
            for item in items_1
        }

        text_2 = {
            normalize(item["content"])
            for item in items_2
        }

        return bool(text_1) and text_1 == text_2

    @staticmethod
    def compare_examination_documents(
        doc_id_1: str,
        doc_id_2: str,
        comparison_type: str = "general",
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare two documents using only chunks visible to the caller.

        Question numbers are aligned explicitly. This structural comparison
        does not independently establish that an answer key is authoritative.
        """

        if not doc_id_1 or not doc_id_2:
            raise ValueError("Both document IDs are required.")

        if doc_id_1 == doc_id_2:
            raise ValueError(
                "The same document cannot be compared with itself."
            )

        chunks_1 = vector_store.get_document_chunks(
            doc_id_1,
            owner_id=owner_id,
            session_id=session_id,
        )

        chunks_2 = vector_store.get_document_chunks(
            doc_id_2,
            owner_id=owner_id,
            session_id=session_id,
        )

        if not chunks_1 or not chunks_2:
            raise ValueError(
                "One or both documents are missing or are not accessible "
                "within the requested owner/session."
            )

        questions_1 = RAGEngine._extract_question_map(chunks_1)
        questions_2 = RAGEngine._extract_question_map(chunks_2)

        ids_1 = set(questions_1)
        ids_2 = set(questions_2)

        common_ids = sorted(
            ids_1.intersection(ids_2),
            key=RAGEngine._question_sort_key,
        )

        only_1 = sorted(
            ids_1 - ids_2,
            key=RAGEngine._question_sort_key,
        )

        only_2 = sorted(
            ids_2 - ids_1,
            key=RAGEngine._question_sort_key,
        )

        aligned = []

        for question_id in common_ids:
            source_1 = questions_1[question_id]
            source_2 = questions_2[question_id]

            text_matches = RAGEngine._text_matches(
                source_1,
                source_2,
            )

            aligned.append({
                "question_number": question_id,
                "document_1": source_1,
                "document_2": source_2,
                "status": "matched_question_number",
                "text_matches": text_matches,
            })

        unmatched = {
            "document_1_only": [
                {
                    "question_number": question_id,
                    "pages": sorted({
                        item["page_number"]
                        for item in questions_1[question_id]
                    }),
                }
                for question_id in only_1
            ],
            "document_2_only": [
                {
                    "question_number": question_id,
                    "pages": sorted({
                        item["page_number"]
                        for item in questions_2[question_id]
                    }),
                }
                for question_id in only_2
            ],
        }

        # These are structural differences in question-number coverage,
        # not proof of an incorrect answer key.
        discrepancies = []

        for question_id in only_1:
            discrepancies.append({
                "type": "QUESTION_NUMBER_MISSING_FROM_DOCUMENT_2",
                "document": doc_id_1,
                "question_number": question_id,
                "pages": sorted({
                    item["page_number"]
                    for item in questions_1[question_id]
                }),
            })

        for question_id in only_2:
            discrepancies.append({
                "type": "QUESTION_NUMBER_MISSING_FROM_DOCUMENT_1",
                "document": doc_id_2,
                "question_number": question_id,
                "pages": sorted({
                    item["page_number"]
                    for item in questions_2[question_id]
                }),
            })

        name_1 = chunks_1[0].doc_name
        name_2 = chunks_2[0].doc_name

        return {
            "document_1": {
                "doc_id": doc_id_1,
                "name": name_1,
                "pages": max(chunk.page_number for chunk in chunks_1),
            },
            "document_2": {
                "doc_id": doc_id_2,
                "name": name_2,
                "pages": max(chunk.page_number for chunk in chunks_2),
            },
            "comparison_type": comparison_type,
            "common_question_count": len(common_ids),
            "common_topics_count": len(common_ids),
            "matched_question_numbers": common_ids,
            "unmatched_question_numbers": unmatched,
            "aligned_questions": aligned,
            "question_comparison": aligned,
            "discrepancies_detected": discrepancies,
            "comparison_status": "STRUCTURAL_COMPARISON_ONLY",
            "comparison_note": (
                "Question-number alignment and source-text comparison only. "
                "A matched question number does not prove that the question "
                "or answer is correct. Unmatched numbers indicate structural "
                "differences, not confirmed answer-key errors. Review the "
                "cited source pages before confirming a discrepancy."
            ),
            "recommendation": (
                "Review the aligned and unmatched source pages and verify "
                "suspected answer-key differences against the authoritative "
                "document."
            ),
        }

    @staticmethod
    def format_citations(
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[DocumentCitation]:
        citations = []

        for item in retrieved_chunks:
            source_text = item.get("raw_content")

            if source_text is None:
                source_text = item.get("content", "")

            snippet = str(source_text or "").strip()

            if not snippet:
                continue

            if len(snippet) > 200:
                snippet = snippet[:200].rstrip() + "..."

            citations.append(
                DocumentCitation(
                    doc_id=item["doc_id"],
                    doc_name=item["doc_name"],
                    page_number=item["page_number"],
                    snippet=snippet,
                    confidence=item.get("relevance_score", 0.0),
                )
            )

        return citations


rag_engine = RAGEngine()
