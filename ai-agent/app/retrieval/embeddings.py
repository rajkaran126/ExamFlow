
"""Provider-independent embedding interface for EXAMFLOW AI.

External embedding API implementations will be supplied separately.
This module defines the contract and validates embedding responses.
"""

from abc import ABC, abstractmethod
import math
from typing import List, Sequence


class EmbeddingProvider(ABC):
    """Base interface for interchangeable embedding providers."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the expected embedding vector dimension."""
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        """Generate one embedding for each supplied document."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a search query."""
        raise NotImplementedError


class EmbeddingValidationError(ValueError):
    """Raised when an embedding response is invalid."""


def validate_embedding(
    embedding: Sequence[float],
    expected_dimensions: int
) -> List[float]:
    """Validate and normalize the representation of an embedding."""

    if expected_dimensions <= 0:
        raise EmbeddingValidationError(
            "Expected embedding dimensions must be positive."
        )

    if not isinstance(embedding, (list, tuple)):
        raise EmbeddingValidationError(
            "Embedding must be a list or tuple."
        )

    if len(embedding) != expected_dimensions:
        raise EmbeddingValidationError(
            f"Expected {expected_dimensions} dimensions, "
            f"received {len(embedding)}."
        )

    validated = []

    for value in embedding:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EmbeddingValidationError(
                "Embedding values must be numeric."
            )

        number = float(value)

        if not math.isfinite(number):
            raise EmbeddingValidationError(
                "Embedding contains a non-finite value."
            )

        validated.append(number)

    return validated


def validate_document_embeddings(
    embeddings: Sequence[Sequence[float]],
    expected_count: int,
    expected_dimensions: int
) -> List[List[float]]:
    """Validate batch size and every returned embedding."""

    if len(embeddings) != expected_count:
        raise EmbeddingValidationError(
            f"Expected {expected_count} embeddings, "
            f"received {len(embeddings)}."
        )

    return [
        validate_embedding(item, expected_dimensions)
        for item in embeddings
    ]
