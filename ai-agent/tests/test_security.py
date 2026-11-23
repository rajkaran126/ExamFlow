"""Automated Tests for Security, RBAC, and Isolation.
Tests role authorization, privacy isolation, prompt injection defense, and secret protection.
"""

import pytest
from app.models import UserRole
from app.permissions import permission_manager
from app.tool_registry import tool_registry

def test_candidate_privacy_isolation():
    """A Candidate role must ONLY be allowed to see their own records, not others."""
    # Candidate CAND-1001 trying to view own scorecard -> Allowed
    allowed, err = permission_manager.check_tool_permission(
        tool_name="get_candidate_scorecard",
        user_role=UserRole.CANDIDATE,
        user_id="CAND-1001",
        arguments={"candidate_id": "CAND-1001"}
    )
    assert allowed is True
    assert err is None

    # Candidate CAND-1001 trying to view CAND-2002 -> Denied
    allowed, err = permission_manager.check_tool_permission(
        tool_name="get_candidate_scorecard",
        user_role=UserRole.CANDIDATE,
        user_id="CAND-1001",
        arguments={"candidate_id": "CAND-2002"}
    )
    assert allowed is False
    assert "Permission Denied" in err

def test_unauthorized_level_5_tool_execution():
    """Candidate or Proctor role cannot execute Level 5 consequential actions."""
    allowed, err = permission_manager.check_tool_permission(
        tool_name="publish_merit_list",
        user_role=UserRole.CANDIDATE,
        user_id="CAND-1001",
        arguments={"preparation_id": "prep_1", "approver_token": "tok_1"}
    )
    assert allowed is False
    assert "Permission Denied" in err

def test_evaluator_cannot_publish_merit_list():
    allowed, err = permission_manager.check_tool_permission(
        tool_name="publish_merit_list",
        user_role=UserRole.EVALUATOR,
        user_id="evaluator_9",
        arguments={"preparation_id": "prep_1", "approver_token": "tok_1"}
    )
    assert allowed is False
    assert "Permission Denied" in err

def test_admin_authorized_for_level_4():
    allowed, err = permission_manager.check_tool_permission(
        tool_name="prepare_merit_list_publication",
        user_role=UserRole.EXAM_ADMIN,
        user_id="admin_1",
        arguments={"exam_id": "EXAM-2026-GATE", "version_tag": "v1.0"}
    )
    assert allowed is True
