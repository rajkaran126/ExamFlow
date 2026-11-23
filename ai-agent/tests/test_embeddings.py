
import pytest

from app.retrieval.embeddings import (
    EmbeddingProvider,
    EmbeddingValidationError,
    validate_embedding,
    validate_document_embeddings,
)


class MockEmbeddingProvider(EmbeddingProvider):

    @property
    def dimensions(self):
        return 3

    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


def test_mock_provider_generates_document_embeddings():
    provider = MockEmbeddingProvider()

    result = provider.embed_documents(["Question one", "Question two"])

    assert len(result) == 2
    assert all(len(item) == 3 for item in result)


def test_mock_provider_generates_query_embedding():
    provider = MockEmbeddingProvider()

    result = provider.embed_query("Find answer key")

    assert result == [0.1, 0.2, 0.3]


def test_valid_embedding_is_accepted():
    result = validate_embedding([0.1, 0.2, 0.3], 3)

    assert result == [0.1, 0.2, 0.3]


def test_wrong_embedding_dimension_is_rejected():
    with pytest.raises(EmbeddingValidationError):
        validate_embedding([0.1, 0.2], 3)


def test_non_numeric_embedding_is_rejected():
    with pytest.raises(EmbeddingValidationError):
        validate_embedding([0.1, "invalid", 0.3], 3)


def test_non_finite_embedding_is_rejected():
    with pytest.raises(EmbeddingValidationError):
        validate_embedding([0.1, float("nan"), 0.3], 3)


def test_boolean_embedding_value_is_rejected():
    with pytest.raises(EmbeddingValidationError):
        validate_embedding([0.1, True, 0.3], 3)


def test_batch_embedding_count_is_validated():
    with pytest.raises(EmbeddingValidationError):
        validate_document_embeddings(
            [[0.1, 0.2, 0.3]],
            expected_count=2,
            expected_dimensions=3,
        )


def test_batch_embeddings_are_validated():
    result = validate_document_embeddings(
        [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        expected_count=2,
        expected_dimensions=3,
    )

    assert len(result) == 2
    assert result[1] == [0.4, 0.5, 0.6]
