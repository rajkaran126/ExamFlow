
"""Security tests for EXAMFLOW AI session ownership and isolation."""

import pytest

from app.context_manager import ContextManager
from app.models import ChatMessage, UserRole


@pytest.fixture
def manager():
    return ContextManager()


def test_session_cannot_be_accessed_by_another_user(manager):
    manager.get_or_create_session(
        "session_1", "user_1", UserRole.CANDIDATE
    )

    with pytest.raises(PermissionError, match="another user"):
        manager.get_session("session_1", "user_2")


def test_session_owner_cannot_be_replaced(manager):
    manager.get_or_create_session(
        "session_1", "user_1", UserRole.CANDIDATE
    )

    with pytest.raises(PermissionError):
        manager.get_or_create_session(
            "session_1", "user_2", UserRole.EXAM_ADMIN
        )

    session = manager.sessions["session_1"]
    assert session.user_id == "user_1"
    assert session.user_role == UserRole.CANDIDATE


def test_session_role_cannot_be_changed(manager):
    manager.get_or_create_session(
        "session_1", "user_1", UserRole.CANDIDATE
    )

    with pytest.raises(PermissionError, match="role"):
        manager.get_or_create_session(
            "session_1", "user_1", UserRole.EXAM_ADMIN
        )


def test_different_users_have_independent_histories(manager):
    session_a = manager.get_or_create_session(
        "session_a", "user_a", UserRole.CANDIDATE
    )
    session_b = manager.get_or_create_session(
        "session_b", "user_b", UserRole.CANDIDATE
    )

    session_a.add_message(
        ChatMessage(role="user", content="Private message A")
    )
    session_b.add_message(
        ChatMessage(role="user", content="Private message B")
    )

    history_a = session_a.get_recent_history()
    history_b = session_b.get_recent_history()

    assert len(history_a) == 1
    assert len(history_b) == 1
    assert history_a[0].content == "Private message A"
    assert history_b[0].content == "Private message B"


def test_session_clear_removes_history_and_pending_state(manager):
    session = manager.get_or_create_session(
        "session_1", "user_1", UserRole.EXAM_ADMIN
    )

    session.add_message(
        ChatMessage(role="user", content="Private information")
    )

    session.active_candidate_id = "CAND-1001"
    session.active_shift_id = "SHIFT-2"

    session.clear()

    assert session.history == []
    assert session.attached_docs == {}
    assert session.pending_actions == {}
    assert session.active_candidate_id is None
    assert session.active_shift_id is None

    # Clearing data must not change ownership.
    assert session.user_id == "user_1"
    assert session.user_role == UserRole.EXAM_ADMIN


def test_user_cannot_delete_another_users_session(manager):
    manager.get_or_create_session(
        "session_1", "user_1", UserRole.CANDIDATE
    )

    with pytest.raises(PermissionError, match="another user"):
        manager.delete_session("session_1", "user_2")

    assert "session_1" in manager.sessions


def test_owner_can_delete_own_session(manager):
    manager.get_or_create_session(
        "session_1", "user_1", UserRole.CANDIDATE
    )

    deleted = manager.delete_session("session_1", "user_1")

    assert deleted is True
    assert "session_1" not in manager.sessions


def test_expired_sessions_are_cleaned_up(manager):
    session = manager.get_or_create_session(
        "old_session", "user_1", UserRole.CANDIDATE
    )

    session.last_accessed -= 2 * 3600

    removed = manager.cleanup_expired_sessions(max_idle_hours=1)

    assert removed == 1
    assert "old_session" not in manager.sessions


def test_invalid_expiry_period_is_rejected(manager):
    with pytest.raises(ValueError):
        manager.cleanup_expired_sessions(max_idle_hours=0)
