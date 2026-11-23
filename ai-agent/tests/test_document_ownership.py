
import pytest

from app.models import DocumentChunk
from app.retrieval.vector_store import VectorStore
from app.retrieval.rag_engine import RAGEngine


@pytest.fixture
def store():
    return VectorStore()


def make_chunk(doc_id, owner_id, session_id, content):
    return DocumentChunk(
        doc_id=doc_id,
        doc_name=f"{doc_id}.pdf",
        page_number=1,
        content=content,
        owner_id=owner_id,
        session_id=session_id,
    )


def test_owner_can_retrieve_own_document(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Negative marking is one third."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    results = store.search(
        "negative marking",
        owner_id="user-a",
    )

    assert len(results) == 1
    assert results[0][0].doc_id == "doc-a"


def test_other_user_cannot_search_document(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Confidential examination document."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    results = store.search(
        "confidential examination",
        owner_id="user-b",
    )

    assert results == []


def test_forged_document_id_does_not_bypass_owner_check(store):
    chunk = make_chunk(
        "private-doc", "user-a", "session-a",
        "Private answer key information."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    results = store.search(
        "answer key",
        owner_id="user-b",
        doc_ids=["private-doc"],
    )

    assert results == []


def test_page_retrieval_is_owner_scoped(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Page one private content."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    assert store.get_chunks_by_pages(
        "doc-a", [1], "user-a"
    )

    assert store.get_chunks_by_pages(
        "doc-a", [1], "user-b"
    ) == []


def test_document_retrieval_is_owner_scoped(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Private content."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    assert len(store.get_document_chunks("doc-a", "user-a")) == 1
    assert store.get_document_chunks("doc-a", "user-b") == []


def test_missing_owner_identity_is_rejected(store):
    with pytest.raises(PermissionError):
        store.search("private content", owner_id="")


def test_upload_cannot_assign_another_users_owner(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Private content."
    )

    with pytest.raises(PermissionError):
        store.add_chunks(
            [chunk],
            owner_id="user-b",
            session_id="session-b",
        )



def test_session_filter_prevents_cross_session_retrieval(store):
    first = make_chunk(
        "doc-a", "user-a", "session-a",
        "First session document."
    )

    second = make_chunk(
        "doc-b", "user-a", "session-b",
        "Second session document."
    )

    # Upload each document into its own session.
    store.add_chunks(
        [first],
        owner_id="user-a",
        session_id="session-a",
    )

    store.add_chunks(
        [second],
        owner_id="user-a",
        session_id="session-b",
    )

    results = store.search(
        "session document",
        owner_id="user-a",
        session_id="session-b",
    )

    assert len(results) == 1
    assert results[0][0].doc_id == "doc-b"
    assert results[0][0].session_id == "session-b"



def test_chunk_id_cannot_be_reassigned_to_another_owner(store):
    chunk = make_chunk(
        "doc-a", "user-a", "session-a",
        "Original content."
    )

    store.add_chunks([chunk], "user-a", "session-a")

    forged = DocumentChunk(
        chunk_id=chunk.chunk_id,
        doc_id="doc-b",
        doc_name="doc-b.pdf",
        page_number=1,
        content="Forged content.",
        owner_id="user-b",
        session_id="session-b",
    )

    with pytest.raises(PermissionError):
        store.add_chunks([forged], "user-b", "session-b")
