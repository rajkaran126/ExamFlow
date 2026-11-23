
import pytest

from app.models import DocumentChunk
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.vector_store import VectorStore


class MockEmbeddingProvider(EmbeddingProvider):

    @property
    def dimensions(self):
        return 3

    def embed_documents(self, texts):
        results = []

        for text in texts:
            if "cutoff" in text.lower():
                results.append([1.0, 0.0, 0.0])
            else:
                results.append([0.0, 1.0, 0.0])

        return results

    def embed_query(self, text):
        if "qualifying marks" in text.lower():
            return [1.0, 0.0, 0.0]

        return [0.0, 1.0, 0.0]


def make_chunk(chunk_id, content, doc_id="doc1"):
    return DocumentChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        doc_name="exam_rules.pdf",
        page_number=1,
        content=content,
    )


def test_semantic_embeddings_are_generated_and_stored():
    store = VectorStore(MockEmbeddingProvider())

    chunks = [
        make_chunk("c1", "Sectional cutoff is 30 marks."),
        make_chunk("c2", "Proctoring rules and monitoring."),
    ]

    store.add_chunks(chunks)

    assert chunks[0].embedding == [1.0, 0.0, 0.0]
    assert chunks[1].embedding == [0.0, 1.0, 0.0]


def test_semantic_search_returns_relevant_chunk():
    store = VectorStore(MockEmbeddingProvider())

    store.add_chunks([
        make_chunk("c1", "Sectional cutoff is 30 marks."),
        make_chunk("c2", "Proctoring rules and monitoring."),
    ])

    results = store.search("What are the qualifying marks?")

    assert results
    assert results[0][0].chunk_id == "c1"


def test_lexical_fallback_works_without_provider():
    store = VectorStore()

    store.add_chunks([
        make_chunk("c1", "Sectional cutoff is 30 marks."),
        make_chunk("c2", "Proctoring rules and monitoring."),
    ])

    results = store.search("sectional cutoff marks")

    assert results
    assert results[0][0].chunk_id == "c1"


def test_document_scoped_search():
    store = VectorStore()

    store.add_chunks([
        make_chunk("c1", "Sectional cutoff is 30 marks.", "doc1"),
        make_chunk("c2", "Sectional cutoff is 40 marks.", "doc2"),
    ])

    results = store.search(
        "sectional cutoff",
        doc_ids=["doc2"],
    )

    assert results
    assert all(item[0].doc_id == "doc2" for item in results)


def test_invalid_embedding_batch_does_not_partially_index():
    class InvalidProvider(MockEmbeddingProvider):

        def embed_documents(self, texts):
            return [[1.0, 0.0]]  # Wrong dimensions.

    store = VectorStore(InvalidProvider())

    chunks = [
        make_chunk("c1", "Sectional cutoff is 30 marks."),
    ]

    with pytest.raises(ValueError):
        store.add_chunks(chunks)

    assert "c1" not in store.chunks


def test_duplicate_chunk_does_not_duplicate_document_index():
    store = VectorStore()

    chunk = make_chunk("c1", "Sectional cutoff is 30 marks.")

    store.add_chunks([chunk])
    store.add_chunks([chunk])

    assert store.doc_index["doc1"].count("c1") == 1


def test_pgvector_dimensions_are_configurable():
    ddl = VectorStore.get_pgvector_ddl(dimensions=768)

    assert "vector(768)" in ddl


def test_invalid_pgvector_dimensions_are_rejected():
    with pytest.raises(ValueError):
        VectorStore.get_pgvector_ddl(dimensions=0)
