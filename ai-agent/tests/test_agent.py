"""Automated Tests for Agent Orchestration & Multi-step Execution.
Tests the 7-step cycle, shift investigation workflow, tool selection, argument validation,
and result verification.
"""

import pytest
from app.models import ChatRequest, UserRole, PermissionLevel
from app.agent import examflow_agent
from app.tool_registry import tool_registry
from app.services.exam_backend import exam_backend

@pytest.mark.asyncio
async def test_agent_multi_step_shift_investigation():
    """Verify that user asking to investigate Shift 2 triggers the 8-step investigation pipeline."""
    req = ChatRequest(
        message="Investigate why shift 2 has a low qualification rate",
        session_id="test_inv_session",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert res.investigation_report is not None
    assert res.plan is not None
    assert "Shift 2" in res.investigation_report.objective or "SHIFT-2" in res.investigation_report.objective
    
    # Check that tool executions took place
    tool_names = [t.tool_name for t in res.tool_executions]
    assert "get_shift_statistics" in tool_names
    assert "get_answer_key" in tool_names

    # Check that findings identify Section B and proctoring
    findings_str = " ".join(res.investigation_report.findings)
    assert "Section B" in findings_str
    assert "Proctoring" in findings_str
    assert res.verified is True

@pytest.mark.asyncio
async def test_agent_candidate_scorecard_explanation():
    req = ChatRequest(
        message="Explain candidate CAND-1001 scorecard and sectional cutoffs",
        session_id="test_cand_session",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert len(res.tool_executions) > 0
    scorecard_tool = next((t for t in res.tool_executions if t.tool_name == "get_candidate_scorecard"), None)
    assert scorecard_tool is not None
    assert scorecard_tool.status == "success"
    assert scorecard_tool.data["candidate_id"] == "CAND-1001"
    assert scorecard_tool.data["raw_score"] == 85.5

def test_tool_registry_argument_validation():
    # Missing required argument candidate_id
    res = tool_registry.execute_tool(
        tool_name="get_candidate_details",
        arguments={},
        user_role=UserRole.EXAM_ADMIN,
        user_id="admin_1"
    )
    assert res.status == "error"
    assert "candidate_id" in res.error.lower() or "missing" in res.error.lower() or "keyerror" in res.error.lower()

def test_duplicate_consequential_action_prevention():
    # Prepare an action
    prep = exam_backend.prepare_result_report("EXAM-2026-GATE", "SHIFT-1")
    prep_id = prep.preparation_id
    token = prep.approver_token

    # Execute once
    exam_backend.prepared_actions[prep_id] = prep
    res1 = exam_backend.execute_reevaluation(
        preparation_id=prep_id,
        approver_token=token,
        user_role=UserRole.EXAM_ADMIN
    ) if prep.tool_name == "execute_reevaluation" else {"success": True}

    # Attempt to execute already executed action
    from app.models import PreparationStatus
    prep.status = PreparationStatus.EXECUTED
    with pytest.raises(PermissionError) as excinfo:
        exam_backend.execute_reevaluation(prep_id, token, UserRole.EXAM_ADMIN)
    assert "already been executed" in str(excinfo.value).lower()

# --- Regression Tests for ToolCallResult and Data Normalization ---

def test_tool_call_result_successful_dict():
    """Verify ToolCallResult validates with standard dictionary data."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_dict_1",
        tool_name="get_exam_details",
        status="success",
        data={"exam_id": "EXAM-2026-GATE", "max_marks": 100},
        level=PermissionLevel.LEVEL_2_READ,
        verified=True
    )
    assert res.status == "success"
    assert isinstance(res.data, dict)
    assert res.data["exam_id"] == "EXAM-2026-GATE"

def test_tool_call_result_empty_list():
    """Verify ToolCallResult validates without error when data is an empty list."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_empty_list_1",
        tool_name="search_documents",
        status="success",
        data=[],
        level=PermissionLevel.LEVEL_2_READ,
        verified=True
    )
    assert res.status == "success"
    assert res.data == []

def test_tool_call_result_non_empty_list():
    """Verify ToolCallResult validates without error when data is a non-empty list."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_list_1",
        tool_name="search_documents",
        status="success",
        data=[{"chunk_id": "chunk_101", "content": "Negative marking is 1/3"}],
        level=PermissionLevel.LEVEL_2_READ,
        verified=True
    )
    assert res.status == "success"
    assert isinstance(res.data, list)
    assert len(res.data) == 1

def test_tool_call_result_none_data():
    """Verify ToolCallResult validates without error when data is None."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_none_1",
        tool_name="empty_tool",
        status="success",
        data=None,
        level=PermissionLevel.LEVEL_2_READ,
        verified=True
    )
    assert res.status == "success"
    assert res.data is None

def test_tool_call_result_execution_exception():
    """Verify ToolCallResult handles execution exceptions correctly."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_err_1",
        tool_name="failing_tool",
        status="error",
        data=None,
        error="Backend connection timed out after 30 seconds",
        level=PermissionLevel.LEVEL_2_READ,
        verified=False
    )
    assert res.status == "error"
    assert res.data is None
    assert "timed out" in res.error

def test_tool_call_result_permission_denied():
    """Verify ToolCallResult handles permission denial with data=None."""
    from app.models import ToolCallResult, PermissionLevel
    res = ToolCallResult(
        call_id="call_denied_1",
        tool_name="publish_merit_list",
        status="denied",
        data=None,
        error="Permission Denied: Role 'candidate' is not authorized to use tool 'publish_merit_list'.",
        level=PermissionLevel.LEVEL_5_CONSEQUENTIAL,
        verified=False
    )
    assert res.status == "denied"
    assert res.data is None
    assert "Permission Denied" in res.error

def test_search_documents_tool_execution_normalization():
    """Verify execute_tool('search_documents') returns normalized dict with total_results and chunks."""
    res = tool_registry.execute_tool(
        tool_name="search_documents",
        arguments={"query": "nonexistent query term in empty store"},
        user_role=UserRole.EXAM_ADMIN,
        user_id="admin_user"
    )
    assert res.status == "success"
    assert isinstance(res.data, dict)
    assert "total_results" in res.data
    assert "chunks" in res.data
    assert res.data["total_results"] == 0
    assert res.data["chunks"] == []

@pytest.mark.asyncio
async def test_normal_chat_message_flow():
    """Verify sending normal chat messages succeeds without Pydantic ValidationError."""
    normal_messages = [
        "Hello, what can you help me with?",
        "What are the rules for negative marking in GATE 2026?",
        "Explain the sectional cutoff requirements",
        "Summarize document guidelines"
    ]
    for msg in normal_messages:
        req = ChatRequest(
            message=msg,
            session_id=f"test_sess_{hash(msg)}",
            user_role=UserRole.EXAM_ADMIN
        )
        res = await examflow_agent.chat(req)
        assert res is not None
        assert res.reply is not None
        assert len(res.reply) > 0

@pytest.mark.asyncio
async def test_chat_seven_step_investigation_cycle():
    """Verify chat endpoint delivers full 7-step investigation cycle answer with PS-072 examples."""
    req = ChatRequest(
        message="Explain your seven-step autonomous investigation cycle in detail. Give one practical example from PS-072 for each step.",
        session_id="test_sess_seven_steps",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert res.reply is not None
    # Must not be the generic welcome loop
    assert not res.reply.startswith("**EXAMFLOW AI System Active**")
    # Must contain 7 steps
    for step in ["Understand", "Plan", "Investigate", "Retrieve", "Execute", "Verify", "Respond"]:
        assert step in res.reply, f"Missing step: {step}"
    # Must contain PS-072 practical examples
    assert "PS-072" in res.reply
    assert "Shift 2" in res.reply or "SHIFT-2" in res.reply

@pytest.mark.asyncio
async def test_chat_greeting():
    """Verify chat endpoint delivers friendly greeting without generic welcome loop."""
    req = ChatRequest(
        message="Hello, can you help me?",
        session_id="test_sess_greeting",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert "EXAMFLOW AI" in res.reply
    assert not res.reply.startswith("**EXAMFLOW AI System Active**")

@pytest.mark.asyncio
async def test_chat_negative_marking_and_cutoffs():
    """Verify chat endpoint delivers negative marking and sectional cutoffs."""
    req = ChatRequest(
        message="What are the negative marking rules and sectional cutoffs?",
        session_id="test_sess_neg_marking",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert "-1/3" in res.reply or "0.33" in res.reply
    assert "Section A" in res.reply
    assert "Section B" in res.reply

@pytest.mark.asyncio
async def test_chat_document_search_empty_store():
    """Verify searching documents when no PDFs are uploaded gives clear notice."""
    req = ChatRequest(
        message="Explain what is in this pdf",
        session_id="test_sess_doc_search",
        user_role=UserRole.EXAM_ADMIN
    )
    res = await examflow_agent.chat(req)
    assert res is not None
    assert ("No relevant document chunks were found" in res.reply or 
            "upload" in res.reply.lower())
    assert any(t.tool_name == "search_documents" for t in res.tool_executions)

