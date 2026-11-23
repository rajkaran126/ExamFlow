
import pytest

from app.models import DocumentChunk
from app.retrieval.vector_store import VectorStore
from app.retrieval import rag_engine as rag_module
from app.retrieval.rag_engine import RAGEngine


@pytest.fixture
def isolated_store(monkeypatch):
    store = VectorStore()
    monkeypatch.setattr(rag_module, "vector_store", store)
    return store


def make_chunk(chunk_id, doc_id, name, page, content):
    return DocumentChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        doc_name=name,
        page_number=page,
        content=content,
    )


def test_citation_uses_original_document_text():
    result = [{
        "doc_id": "doc1",
        "doc_name": "rules.pdf",
        "page_number": 2,
        "raw_content": "Negative marking is applicable.",
        "content": "[UNTRUSTED DOCUMENT CONTENT]",
        "relevance_score": 0.85,
    }]

    citations = RAGEngine.format_citations(result)

    assert len(citations) == 1
    assert citations[0].snippet == "Negative marking is applicable."
    assert citations[0].page_number == 2
    assert citations[0].confidence == 0.85


def test_empty_citation_content_is_skipped():
    result = [{
        "doc_id": "doc1",
        "doc_name": "rules.pdf",
        "page_number": 1,
        "raw_content": "   ",
    }]

    assert RAGEngine.format_citations(result) == []


def test_search_preserves_raw_and_wrapped_content(isolated_store):
    isolated_store.add_chunks([
        make_chunk(
            "c1",
            "doc1",
            "rules.pdf",
            1,
            "Sectional cutoff is 25 marks.",
        )
    ])

    results = RAGEngine.search_documents("sectional cutoff")

    assert len(results) == 1
    assert results[0]["raw_content"] == "Sectional cutoff is 25 marks."
    assert results[0]["content"] != results[0]["raw_content"]


def test_document_comparison_aligns_question_numbers(isolated_store):
    isolated_store.add_chunks([
        make_chunk(
            "q1",
            "question_doc",
            "questions.pdf",
            1,
            "Question 42: What is the time complexity of Dijkstra?",
        ),
        make_chunk(
            "k1",
            "key_doc",
            "answer_key.pdf",
            2,
            "Question 42: Option B",
        ),
    ])

    result = RAGEngine.compare_examination_documents(
        "question_doc",
        "key_doc",
    )

    assert result["common_topics_count"] == 1
    assert result["aligned_questions"][0]["question_number"] == 42
    assert result["aligned_questions"][0]["text_matches"] is False
    assert result["comparison_status"] == "STRUCTURAL_COMPARISON_ONLY"


def test_comparison_reports_unmatched_question_numbers(isolated_store):
    isolated_store.add_chunks([
        make_chunk(
            "q1",
            "question_doc",
            "questions.pdf",
            1,
            "Question 10: Explain machine learning.",
        ),
        make_chunk(
            "k1",
            "key_doc",
            "answer_key.pdf",
            1,
            "Question 11: Option C",
        ),
    ])

    result = RAGEngine.compare_examination_documents(
        "question_doc",
        "key_doc",
    )

    assert result["common_topics_count"] == 0
    assert len(result["discrepancies_detected"]) == 2


def test_comparison_rejects_same_document(isolated_store):
    with pytest.raises(ValueError):
        RAGEngine.compare_examination_documents("doc1", "doc1")


def test_comparison_rejects_missing_document(isolated_store):
    with pytest.raises(ValueError):
        RAGEngine.compare_examination_documents("missing1", "missing2")


def test_page_retrieval_is_document_scoped(isolated_store):
    isolated_store.add_chunks([
        make_chunk("c1", "doc1", "one.pdf", 1, "Page one."),
        make_chunk("c2", "doc2", "two.pdf", 1, "Page two."),
    ])

    results = RAGEngine.retrieve_document_chunks("doc1", [1])

    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"


def test_invalid_search_inputs_return_empty_results(isolated_store):
    assert RAGEngine.search_documents("") == []
    assert RAGEngine.search_documents("valid query", top_k=0) == []
