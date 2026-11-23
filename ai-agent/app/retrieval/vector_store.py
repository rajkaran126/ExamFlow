
"""Hybrid in-memory vector store for EXAMFLOW AI.

Supports provider-generated semantic embeddings, lexical fallback,
document/page retrieval, and owner/session isolation.

Legacy calls are restricted to a dedicated __legacy__ namespace.
"""

import math
import re
from typing import Dict, List, Optional, Tuple

from app.models import DocumentChunk
from app.retrieval.embeddings import (
    EmbeddingProvider,
    validate_embedding,
    validate_document_embeddings,
)

LEGACY_OWNER = "__legacy__"
LEGACY_SESSION = "__legacy__"


class VectorStore:
    """Hybrid vector store with explicit document ownership."""

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.chunks: Dict[str, DocumentChunk] = {}
        self.doc_index: Dict[str, List[str]] = {}
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.embedding_provider = embedding_provider

    def set_embedding_provider(
        self,
        provider: Optional[EmbeddingProvider],
    ) -> None:
        self.embedding_provider = provider

    @staticmethod
    def _identity(owner_id=None, session_id=None):
        """Resolve identity.

        No identity selects the isolated legacy namespace.
        An owner without a session can access all their sessions.
        An explicitly supplied session restricts access to that session.
        """
        if owner_id is None:
            if session_id is not None:
                raise PermissionError(
                    "An explicit owner identity is required "
                    "when session_id is supplied."
                )
            return LEGACY_OWNER, LEGACY_SESSION

        if not isinstance(owner_id, str) or not owner_id.strip():
            raise PermissionError("A valid owner identity is required.")

        owner_id = owner_id.strip()

        if session_id is not None:
            if not isinstance(session_id, str) or not session_id.strip():
                raise ValueError("A valid session_id is required.")
            session_id = session_id.strip()

        return owner_id, session_id

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Validate, stamp ownership, optionally embed, then index chunks."""

        if not chunks:
            return

        prepared = list(chunks)

        if any(not isinstance(chunk, DocumentChunk) for chunk in prepared):
            raise TypeError("Every indexed item must be a DocumentChunk.")

        resolved_owner, resolved_session = self._identity(
            owner_id,
            session_id,
        )

        # When an explicit owner is supplied without a session,
        # infer the session from the uploaded chunks if possible.
        if owner_id is not None and resolved_session is None:
            existing_sessions = {
                chunk.session_id
                for chunk in prepared
                if getattr(chunk, "session_id", None)
            }

            if len(existing_sessions) > 1:
                raise ValueError(
                    "An upload batch cannot contain multiple sessions."
                )

            resolved_session = (
                next(iter(existing_sessions))
                if existing_sessions
                else LEGACY_SESSION
            )

        seen_ids = set()

        # Validate the complete batch before modifying the store.
        for chunk in prepared:
            if chunk.chunk_id in seen_ids:
                raise ValueError("Duplicate chunk_id found in upload batch.")

            seen_ids.add(chunk.chunk_id)

            existing = self.chunks.get(chunk.chunk_id)

            if existing is not None:
                if (
                    existing.owner_id != resolved_owner
                    or existing.session_id != resolved_session
                    or existing.doc_id != chunk.doc_id
                ):
                    raise PermissionError(
                        "An existing chunk cannot be reassigned to "
                        "another owner, session, or document."
                    )

            chunk_owner = getattr(chunk, "owner_id", None)
            chunk_session = getattr(chunk, "session_id", None)

            if chunk_owner not in (None, resolved_owner):
                raise PermissionError(
                    "Chunk owner does not match upload owner."
                )

            if chunk_session not in (None, resolved_session):
                raise PermissionError(
                    "Chunk session does not match upload session."
                )

        # Generate and validate embeddings before indexing.
        generated_embeddings = {}

        if self.embedding_provider is not None:
            dimensions = self.embedding_provider.dimensions

            missing = [
                chunk for chunk in prepared
                if chunk.embedding is None
            ]

            if missing:
                generated = self.embedding_provider.embed_documents(
                    [chunk.content for chunk in missing]
                )

                validated = validate_document_embeddings(
                    generated,
                    expected_count=len(missing),
                    expected_dimensions=dimensions,
                )

                generated_embeddings = {
                    chunk.chunk_id: embedding
                    for chunk, embedding in zip(missing, validated)
                }

            for chunk in prepared:
                candidate = (
                    generated_embeddings.get(chunk.chunk_id)
                    if chunk.embedding is None
                    else chunk.embedding
                )
                validate_embedding(candidate, dimensions)

        # All validation succeeded. Stamp identity and index.
        for chunk in prepared:
            chunk.owner_id = resolved_owner
            chunk.session_id = resolved_session

            if chunk.chunk_id in generated_embeddings:
                chunk.embedding = generated_embeddings[chunk.chunk_id]

            self.chunks[chunk.chunk_id] = chunk

            ids = self.doc_index.setdefault(chunk.doc_id, [])

            if chunk.chunk_id not in ids:
                ids.append(chunk.chunk_id)

        self._rebuild_tfidf_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())

    def _rebuild_tfidf_index(self) -> None:
        total = len(self.chunks)

        if total == 0:
            self.vocabulary = {}
            self.idf = {}
            return

        frequencies: Dict[str, int] = {}

        for chunk in self.chunks.values():
            for token in set(self._tokenize(chunk.content)):
                frequencies[token] = frequencies.get(token, 0) + 1

        self.idf = {
            token: math.log((1 + total) / (1 + count)) + 1.0
            for token, count in frequencies.items()
        }

        self.vocabulary = {
            word: index
            for index, word in enumerate(sorted(self.idf))
        }

    @staticmethod
    def _cosine_similarity(
        first: List[float],
        second: List[float],
    ) -> float:
        if len(first) != len(second):
            return 0.0

        dot = sum(a * b for a, b in zip(first, second))
        norm_a = math.sqrt(sum(value * value for value in first))
        norm_b = math.sqrt(sum(value * value for value in second))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _lexical_search(
        self,
        query: str,
        candidates: List[DocumentChunk],
        top_k: int,
    ) -> List[Tuple[DocumentChunk, float]]:
        tokens = self._tokenize(query)

        if not tokens:
            return []

        query_tf: Dict[str, int] = {}

        for token in tokens:
            query_tf[token] = query_tf.get(token, 0) + 1

        query_weights = {
            token: count * self.idf.get(token, 1.0)
            for token, count in query_tf.items()
        }

        query_norm = math.sqrt(
            sum(weight * weight for weight in query_weights.values())
        )

        if query_norm == 0:
            return []

        scores = []

        for chunk in candidates:
            chunk_tf: Dict[str, int] = {}

            for token in self._tokenize(chunk.content):
                chunk_tf[token] = chunk_tf.get(token, 0) + 1

            weights = {
                token: count * self.idf.get(token, 1.0)
                for token, count in chunk_tf.items()
            }

            chunk_norm = math.sqrt(
                sum(value * value for value in weights.values())
            )

            if chunk_norm == 0:
                continue

            dot = sum(
                weight * query_weights.get(token, 0.0)
                for token, weight in weights.items()
            )

            similarity = dot / (query_norm * chunk_norm)

            if similarity > 0.05:
                scores.append((chunk, round(similarity, 4)))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_k]

    def _semantic_search(
        self,
        query: str,
        candidates: List[DocumentChunk],
        top_k: int,
    ) -> List[Tuple[DocumentChunk, float]]:
        provider = self.embedding_provider

        if provider is None:
            return []

        query_embedding = validate_embedding(
            provider.embed_query(query),
            provider.dimensions,
        )

        scores = []

        for chunk in candidates:
            if chunk.embedding is None:
                continue

            embedding = validate_embedding(
                chunk.embedding,
                provider.dimensions,
            )

            similarity = self._cosine_similarity(
                query_embedding,
                embedding,
            )

            if similarity > 0:
                scores.append((chunk, round(similarity, 4)))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_k]

    def _filter_by_identity(
        self,
        owner_id: Optional[str],
        session_id: Optional[str],
    ):
        return self._identity(owner_id, session_id)

    def search(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 4,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search within the requested owner/session namespace."""

        if not isinstance(query, str) or not query.strip():
            return []

        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k <= 0
        ):
            return []

        resolved_owner, resolved_session = self._filter_by_identity(
            owner_id,
            session_id,
        )

        candidates = [
            chunk
            for chunk in self.chunks.values()
            if chunk.owner_id == resolved_owner
            and (
                resolved_session is None
                or chunk.session_id == resolved_session
            )
            and (not doc_ids or chunk.doc_id in doc_ids)
        ]

        if not candidates:
            return []

        semantic_ready = (
            self.embedding_provider is not None
            and all(chunk.embedding is not None for chunk in candidates)
        )

        if semantic_ready:
            return self._semantic_search(query, candidates, top_k)

        return self._lexical_search(query, candidates, top_k)

    def get_chunks_by_pages(
        self,
        doc_id: str,
        page_numbers: List[int],
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[DocumentChunk]:
        if not page_numbers:
            return []

        resolved_owner, resolved_session = self._filter_by_identity(
            owner_id,
            session_id,
        )

        return [
            chunk
            for chunk in self.get_document_chunks(
                doc_id,
                owner_id=resolved_owner,
                session_id=resolved_session,
            )
            if chunk.page_number in page_numbers
        ]

    def get_document_chunks(
        self,
        doc_id: str,
        owner_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[DocumentChunk]:
        resolved_owner, resolved_session = self._filter_by_identity(
            owner_id,
            session_id,
        )

        return [
            self.chunks[chunk_id]
            for chunk_id in self.doc_index.get(doc_id, [])
            if chunk_id in self.chunks
            and self.chunks[chunk_id].owner_id == resolved_owner
            and (
                resolved_session is None
                or self.chunks[chunk_id].session_id == resolved_session
            )
        ]

    @staticmethod
    def get_pgvector_ddl(dimensions: int = 1536) -> str:
        if (
            isinstance(dimensions, bool)
            or not isinstance(dimensions, int)
            or dimensions <= 0
        ):
            raise ValueError(
                "Embedding dimensions must be a positive integer."
            )

        return f"""
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id VARCHAR(64) PRIMARY KEY,
            doc_id VARCHAR(64) NOT NULL,
            doc_name VARCHAR(255) NOT NULL,
            owner_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            page_number INT NOT NULL,
            content TEXT NOT NULL,
            embedding vector({dimensions}),
            metadata JSONB DEFAULT '{{}}'::jsonb,
            is_ocr BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc_id
        ON document_chunks(doc_id);

        CREATE INDEX IF NOT EXISTS idx_doc_chunks_owner_session
        ON document_chunks(owner_id, session_id);

        CREATE INDEX IF NOT EXISTS idx_doc_chunks_embedding
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """


vector_store = VectorStore()
