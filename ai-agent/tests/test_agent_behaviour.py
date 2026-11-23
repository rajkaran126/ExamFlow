
"""End-to-end behaviour tests for EXAMFLOW AI.

Covers malformed tool calls, failed backend operations, tool execution,
response synthesis, and incomplete investigation evidence.
"""

import pytest

from app.models import (
    ChatRequest,
    ToolCallResult,
    UserRole,
    PermissionLevel,
)
from app.agent import examflow_agent
from app.orchestrator import agent_orchestrator
from app.tool_registry import tool_registry
from app.llama_client import llama_client


def make_tool_result(
    call_id,
    tool_name,
    status="success",
    data=None,
    error=None,
    verified=True,
):
    return ToolCallResult(
        call_id=call_id,
        tool_name=tool_name,
        status=status,
        data=data,
        error=error,
        level=PermissionLevel.LEVEL_2_READ,
        verified=verified,
    )


def test_invalid_json_tool_arguments_are_rejected(monkeypatch):
    """Malformed JSON must not reach the tool registry."""

    def unexpected_execution(**kwargs):
        pytest.fail("Tool registry must not execute malformed arguments")

    monkeypatch.setattr(
        tool_registry,
        "execute_tool",
        unexpected_execution,
    )

    result = agent_orchestrator._execute_llm_tool_call(
        {
            "id": "invalid_json_call",
            "function": {
                "name": "get_exam_details",
                "arguments": '{"exam_id": ',
            },
        },
        0,
        None,
        None,
    )

    assert result.status == "error"
    assert result.verified is False
    assert "valid JSON" in result.error


def test_non_object_tool_arguments_are_rejected(monkeypatch):
    """Valid JSON arrays/scalars must not be accepted as argument objects."""

    def unexpected_execution(**kwargs):
        pytest.fail("Tool registry must not execute non-object arguments")

    monkeypatch.setattr(
        tool_registry,
        "execute_tool",
        unexpected_execution,
    )

    result = agent_orchestrator._execute_llm_tool_call(
        {
            "id": "array_arguments_call",
            "function": {
                "name": "get_exam_details",
                "arguments": '["EXAM-2026-GATE"]',
            },
        },
        0,
        None,
        None,
    )

    assert result.status == "error"
    assert result.verified is False
    assert "JSON object" in result.error


@pytest.mark.asyncio
async def test_failed_tool_execution_is_not_marked_verified(monkeypatch):
    """A failed backend tool must produce an unverified response."""

    async def fake_llama(messages, tools=None):
        if tools is not None:
            return {
                "content": "I will retrieve the examination details.",
                "tool_calls": [
                    {
                        "id": "failed_exam_lookup",
                        "type": "function",
                        "function": {
                            "name": "get_exam_details",
                            "arguments": '{"exam_id": "EXAM-2026-GATE"}',
                        },
                    }
                ],
            }

        return {
            "content": "The examination details could not be retrieved."
        }

    def fake_tool_execution(**kwargs):
        return make_tool_result(
            call_id=kwargs.get("call_id", "failed_exam_lookup"),
            tool_name=kwargs["tool_name"],
            status="error",
            error="Backend connection timed out",
            verified=False,
        )

    monkeypatch.setattr(
        llama_client,
        "generate_chat_completion",
        fake_llama,
    )
    monkeypatch.setattr(
        tool_registry,
        "execute_tool",
        fake_tool_execution,
    )

    request = ChatRequest(
        message="Retrieve the examination details",
        session_id="behaviour_failed_tool_session",
        user_role=UserRole.EXAM_ADMIN,
    )

    response = await examflow_agent.chat(request)

    assert response is not None
    assert len(response.tool_executions) == 1
    assert response.tool_executions[0].status == "error"
    assert response.verified is False
    assert "could not be retrieved" in response.reply.lower()


@pytest.mark.asyncio
async def test_successful_tool_execution_reaches_response_synthesis(monkeypatch):
    """Tool output must be passed to the final Llama synthesis call."""

    calls = []

    async def fake_llama(messages, tools=None):
        calls.append(messages)

        if tools is not None:
            return {
                "content": "Retrieving examination details.",
                "tool_calls": [
                    {
                        "id": "successful_exam_lookup",
                        "type": "function",
                        "function": {
                            "name": "get_exam_details",
                            "arguments": '{"exam_id": "EXAM-2026-GATE"}',
                        },
                    }
                ],
            }

        return {
            "content": "The examination details were retrieved successfully."
        }

    def fake_tool_execution(**kwargs):
        return make_tool_result(
            call_id=kwargs.get("call_id", "successful_exam_lookup"),
            tool_name=kwargs["tool_name"],
            data={
                "exam_id": "EXAM-2026-GATE",
                "max_marks": 100,
            },
            verified=True,
        )

    monkeypatch.setattr(
        llama_client,
        "generate_chat_completion",
        fake_llama,
    )
    monkeypatch.setattr(
        tool_registry,
        "execute_tool",
        fake_tool_execution,
    )

    request = ChatRequest(
        message="Retrieve the examination details",
        session_id="behaviour_successful_tool_session",
        user_role=UserRole.EXAM_ADMIN,
    )

    response = await examflow_agent.chat(request)

    assert response is not None
    assert len(calls) == 2
    assert response.tool_executions[0].status == "success"
    assert response.verified is True
    assert "retrieved successfully" in response.reply.lower()

    # The second Llama call must receive the tool result.
    tool_messages = [
        message
        for message in calls[1]
        if message.get("role") == "tool"
    ]

    assert len(tool_messages) == 1
    assert "EXAM-2026-GATE" in tool_messages[0]["content"]


@pytest.mark.asyncio
async def test_investigation_with_failed_backend_evidence_is_unverified(
    monkeypatch,
):
    """An investigation with unavailable backend evidence must disclose it."""

    def failing_tool_execution(**kwargs):
        return make_tool_result(
            call_id=kwargs.get("call_id", "failed_investigation_tool"),
            tool_name=kwargs["tool_name"],
            status="error",
            error="Backend data unavailable",
            verified=False,
        )

    monkeypatch.setattr(
        tool_registry,
        "execute_tool",
        failing_tool_execution,
    )

    request = ChatRequest(
        message="Investigate why shift 2 has a low qualification rate",
        session_id="behaviour_incomplete_investigation",
        user_role=UserRole.EXAM_ADMIN,
    )

    response = await examflow_agent.chat(request)

    assert response is not None
    assert response.investigation_report is not None
    assert response.verified is False
    assert len(response.tool_executions) > 0

    assert any(
        "unavailable" in uncertainty.lower()
        or "could not" in uncertainty.lower()
        for uncertainty in response.investigation_report.uncertainties
    )

    assert (
        "No findings could be verified" in response.reply
        or "unavailable" in response.reply.lower()
    )
