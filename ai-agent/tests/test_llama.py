"""Automated Tests for Llama Integration.
Tests normal completions, timeouts, rate limits, context overflow handling, and streaming.
"""

import pytest
import asyncio
from app.llama_client import LlamaClient
from app.config import settings

@pytest.mark.asyncio
async def test_llama_normal_response():
    client = LlamaClient()
    messages = [
        {"role": "system", "content": "You are EXAMFLOW AI."},
        {"role": "user", "content": "What are the sectional cutoffs for EXAM-2026-GATE?"}
    ]
    resp = await client.generate_chat_completion(messages)
    assert resp is not None
    assert resp["role"] == "assistant"
    assert len(resp["content"]) > 0

@pytest.mark.asyncio
async def test_llama_context_overflow_truncation():
    client = LlamaClient()
    # Construct huge context that exceeds context window heuristic
    huge_message = "GATE 2026 examination guidelines " * 3000
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": huge_message},
        {"role": "user", "content": "What is the qualification rate?"}
    ]
    truncated = client._truncate_context_if_needed(messages)
    assert len(truncated) <= len(messages)
    # Ensure system message is preserved
    assert truncated[0]["role"] == "system"

@pytest.mark.asyncio
async def test_llama_timeout_transparent_error():    # Test client with unreachable URL and low timeout
    client = LlamaClient(
        api_key="test_live_key_simulate",
        base_url="http://192.0.2.1:9999", # Non-routable test IP
        timeout=0.2,
        max_retries=1
    )
    messages = [{"role": "user", "content": "Investigate shift 2"}]
    # Should fall back cleanly without unhandled crash
    resp = await client.generate_chat_completion(messages)
    assert resp is not None
    assert resp["role"] == "assistant"
    assert "Llama" in resp["content"]
    assert "fallback" not in resp["content"].lower()

@pytest.mark.asyncio
async def test_llama_streaming():
    client = LlamaClient()
    messages = [{"role": "user", "content": "Summarize result rules"}]
    tokens = []
    async for token in client.stream_chat_completion(messages):
        tokens.append(token)
    assert len(tokens) > 0
    full_text = "".join(tokens)
    assert len(full_text) > 0

@pytest.mark.asyncio
async def test_missing_llama_credentials():
    """Verify that missing API credentials produce a transparent error."""
    client = LlamaClient(
        api_key="mock_unconfigured",
        base_url="https://api.groq.com/openai/v1"
    )

    messages = [
        {"role": "user", "content": "Explain PS-072"}
    ]

    response = await client.generate_chat_completion(messages)

    assert response is not None
    assert response["role"] == "assistant"
    assert response["tool_calls"] is None
    assert response["error"] == "LLAMA_NOT_CONFIGURED"
    assert "not configured" in response["content"].lower()


@pytest.mark.asyncio
async def test_no_hardcoded_response_without_llama():
    """Verify that examination questions are not answered using hardcoded fallbacks."""
    client = LlamaClient(
        api_key="mock_unconfigured",
        base_url="https://api.groq.com/openai/v1"
    )

    messages = [
        {
            "role": "user",
            "content": "What are the negative marking rules and sectional cutoffs?"
        }
    ]

    response = await client.generate_chat_completion(messages)

    assert response["error"] == "LLAMA_NOT_CONFIGURED"
    assert "not configured" in response["content"].lower()
    assert "25.0" not in response["content"]

@pytest.mark.asyncio
async def test_llama_api_failure_transparent_error():
    """Verify that Llama API failure returns a transparent error and does not silently fall back to generic welcome."""
    client = LlamaClient(
        api_key="live_key_for_testing_123456",
        base_url="http://127.0.0.1:54321", # Unreachable local endpoint
        timeout=0.5,
        max_retries=1
    )
    messages = [{"role": "user", "content": "Explain candidate CAND-1001"}]
    resp = await client.generate_chat_completion(messages)
    assert resp is not None
    assert resp["role"] == "assistant"
    # Should contain transparent error notice

    # Should contain a transparent error notice
    assert (
        "⚠️ **Llama API Request Failed:**" in resp["content"]
        or "⚠️ **Llama" in resp["content"]
        or "timed out" in resp["content"].lower()
    )

    assert (
        "Could not connect" in resp["content"]
        or "Error" in resp["content"]
        or "timed out" in resp["content"].lower()
    )


@pytest.mark.asyncio
async def test_llama_api_failure_credentials_redacted():
    """Verify that API credentials, tokens, and secrets are strictly redacted in error outputs."""
    secret_key = "super_secret_llama_key_abc123"
    client = LlamaClient(
        api_key=secret_key,
        base_url="http://127.0.0.1:54321",
        timeout=0.5,
        max_retries=1
    )
    messages = [{"role": "user", "content": "Investigate shift 2"}]
    resp = await client.generate_chat_completion(messages)
    content = resp.get("content", "")
    # Ensure sensitive key is never in output
    assert secret_key not in content
    assert "super_secret" not in content
