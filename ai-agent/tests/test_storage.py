
import pytest

from app.retrieval.storage import (
    DocumentStorage,
    PostgresVectorStorage,
)


def test_storage_interface_is_abstract():
    with pytest.raises(TypeError):
        DocumentStorage()


def test_storage_requires_database_connection():
    with pytest.raises(ValueError):
        PostgresVectorStorage(None)


def test_storage_rejects_invalid_dimensions():
    class FakeConnection:
        pass

    with pytest.raises(ValueError):
        PostgresVectorStorage(FakeConnection(), dimensions=0)


def test_storage_accepts_valid_configuration():
    class FakeConnection:
        pass

    store = PostgresVectorStorage(
        FakeConnection(),
        dimensions=768,
    )

    assert store.dimensions == 768


def test_storage_rejects_boolean_dimensions():
    class FakeConnection:
        pass

    with pytest.raises(ValueError):
        PostgresVectorStorage(
            FakeConnection(),
            dimensions=True,
        )


def test_storage_rejects_missing_embedding():
    from app.models import DocumentChunk

    class FakeConnection:
        pass

    store = PostgresVectorStorage(
        FakeConnection(),
        dimensions=3,
    )

    chunk = DocumentChunk(
        doc_id="doc1",
        doc_name="rules.pdf",
        page_number=1,
        content="Sectional cutoff is 30 marks.",
    )

    with pytest.raises(ValueError):
        store.save_chunks([chunk])


def test_storage_rejects_wrong_embedding_dimensions():
    from app.models import DocumentChunk

    class FakeConnection:
        pass

    store = PostgresVectorStorage(
        FakeConnection(),
        dimensions=3,
    )

    chunk = DocumentChunk(
        doc_id="doc1",
        doc_name="rules.pdf",
        page_number=1,
        content="Sectional cutoff is 30 marks.",
        embedding=[0.1, 0.2],
    )

    with pytest.raises(ValueError):
        store.save_chunks([chunk])


def test_empty_page_request_returns_empty_list():
    class FakeConnection:
        pass

    store = PostgresVectorStorage(
        FakeConnection(),
        dimensions=3,
    )

    assert store.get_chunks_by_pages("doc1", []) == []


def test_empty_document_filter_returns_empty_list():
    class FakeConnection:
        pass

    store = PostgresVectorStorage(
        FakeConnection(),
        dimensions=3,
    )

    assert store.search(
        [0.1, 0.2, 0.3],
        doc_ids=[],
    ) == []


def test_pgvector_ddl_uses_configured_dimensions():
    from app.retrieval.vector_store import VectorStore

    ddl = VectorStore.get_pgvector_ddl(dimensions=768)

    assert "vector(768)" in ddl
