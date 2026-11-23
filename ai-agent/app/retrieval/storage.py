
"""Persistent document storage for EXAMFLOW AI.

Provides a storage interface and PostgreSQL/pgvector implementation.
Database connections are injected by the application integration layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.models import DocumentChunk
from app.retrieval.embeddings import validate_embedding


class DocumentStorage(ABC):
    """Contract for persistent document chunk storage."""

    @abstractmethod
    def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_chunks_by_document(
        self, doc_id: str
    ) -> List[DocumentChunk]:
        raise NotImplementedError

    @abstractmethod
    def get_chunks_by_pages(
        self, doc_id: str, page_numbers: List[int]
    ) -> List[DocumentChunk]:
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        embedding: List[float],
        doc_ids: Optional[List[str]] = None,
        top_k: int = 4,
    ) -> List[Tuple[DocumentChunk, float]]:
        raise NotImplementedError


class PostgresVectorStorage(DocumentStorage):
    """PostgreSQL storage adapter using pgvector cosine similarity."""

    def __init__(self, connection, dimensions: int = 1536):
        if connection is None:
            raise ValueError("A PostgreSQL connection is required.")

        if (
            isinstance(dimensions, bool)
            or not isinstance(dimensions, int)
            or dimensions <= 0
        ):
            raise ValueError("Embedding dimensions must be positive.")

        self.connection = connection
        self.dimensions = dimensions

    def initialize_schema(self) -> None:
        """Create the pgvector extension and document storage table."""

        statements = [
            "CREATE EXTENSION IF NOT EXISTS vector",
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id VARCHAR(64) PRIMARY KEY,
                doc_id VARCHAR(64) NOT NULL,
                doc_name VARCHAR(255) NOT NULL,
                page_number INT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({self.dimensions}),
                metadata JSONB DEFAULT '{{}}'::jsonb,
                is_ocr BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE
                    DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc_id
            ON document_chunks(doc_id)
            """,
        ]

        try:
            with self.connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Insert or update chunks using their stable chunk IDs."""

        if not chunks:
            return

        prepared = []

        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(
                    f"Chunk {chunk.chunk_id} has no semantic embedding."
                )

            embedding = validate_embedding(
                chunk.embedding,
                self.dimensions,
            )

            prepared.append((
                chunk.chunk_id,
                chunk.doc_id,
                chunk.doc_name,
                chunk.page_number,
                chunk.content,
                embedding,
                chunk.metadata,
                chunk.is_ocr,
            ))

        sql = """
            INSERT INTO document_chunks (
                chunk_id, doc_id, doc_name, page_number,
                content, embedding, metadata, is_ocr
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s::vector, %s::jsonb, %s
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                doc_id = EXCLUDED.doc_id,
                doc_name = EXCLUDED.doc_name,
                page_number = EXCLUDED.page_number,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                is_ocr = EXCLUDED.is_ocr
        """

        import json

        try:
            with self.connection.cursor() as cursor:
                for item in prepared:
                    values = list(item)
                    values[5] = "[" + ",".join(
                        str(value) for value in item[5]
                    ) + "]"
                    values[6] = json.dumps(item[6])

                    cursor.execute(sql, tuple(values))

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

    @staticmethod
    def _row_to_chunk(row) -> DocumentChunk:
        """Convert a database row into a validated document chunk."""

        import json

        embedding = row[5]

        if isinstance(embedding, str):
            embedding = json.loads(embedding) if embedding.startswith("[") else [
                float(value)
                for value in embedding.strip("[]").split(",")
                if value.strip()
            ]

        metadata = row[6] or {}

        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return DocumentChunk(
            chunk_id=row[0],
            doc_id=row[1],
            doc_name=row[2],
            page_number=row[3],
            content=row[4],
            embedding=embedding,
            metadata=metadata,
            is_ocr=row[7],
        )

    def get_chunks_by_document(
        self, doc_id: str
    ) -> List[DocumentChunk]:
        """Fetch all chunks belonging to one document."""

        sql = """
            SELECT chunk_id, doc_id, doc_name, page_number,
                   content, embedding::text, metadata, is_ocr
            FROM document_chunks
            WHERE doc_id = %s
            ORDER BY page_number, chunk_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(sql, (doc_id,))
            rows = cursor.fetchall()

        return [self._row_to_chunk(row) for row in rows]

    def get_chunks_by_pages(
        self,
        doc_id: str,
        page_numbers: List[int],
    ) -> List[DocumentChunk]:
        """Fetch chunks from selected pages of one document."""

        if not page_numbers:
            return []

        sql = """
            SELECT chunk_id, doc_id, doc_name, page_number,
                   content, embedding::text, metadata, is_ocr
            FROM document_chunks
            WHERE doc_id = %s AND page_number = ANY(%s)
            ORDER BY page_number, chunk_id
        """

        with self.connection.cursor() as cursor:
            cursor.execute(sql, (doc_id, page_numbers))
            rows = cursor.fetchall()

        return [self._row_to_chunk(row) for row in rows]

    def search(
        self,
        embedding: List[float],
        doc_ids: Optional[List[str]] = None,
        top_k: int = 4,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search using pgvector cosine distance."""

        if top_k <= 0:
            return []

        query_embedding = validate_embedding(
            embedding,
            self.dimensions,
        )

        vector_value = "[" + ",".join(
            str(value) for value in query_embedding
        ) + "]"

        if doc_ids is not None and not doc_ids:
            return []

        if doc_ids is None:
            sql = """
                SELECT chunk_id, doc_id, doc_name, page_number,
                       content, embedding::text, metadata, is_ocr,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params = (vector_value, vector_value, top_k)

        else:
            sql = """
                SELECT chunk_id, doc_id, doc_name, page_number,
                       content, embedding::text, metadata, is_ocr,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM document_chunks
                WHERE embedding IS NOT NULL
                  AND doc_id = ANY(%s)
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params = (
                vector_value,
                doc_ids,
                vector_value,
                top_k,
            )

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        return [
            (self._row_to_chunk(row[:8]), float(row[8]))
            for row in rows
        ]
