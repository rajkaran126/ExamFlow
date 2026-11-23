
import copy

import pytest

from app.models import UserRole, PreparationStatus
from app.services.exam_backend import ExamBackendService


@pytest.fixture
def backend():
    """Create a fresh backend for each test."""
    return ExamBackendService()


def test_merit_list_publication_records_approval(backend):
    prep = backend.prepare_merit_list_publication(
        exam_id=backend.exam_id,
        version_tag="v1.0"
    )

    result = backend.publish_merit_list(
        preparation_id=prep.preparation_id,
        approver_token=prep.approver_token,
        user_role=UserRole.EXAM_ADMIN,
        approver_id="admin_1"
    )

    assert result["success"] is True
    assert result["approved_by"] == "admin_1"
    assert prep.status == PreparationStatus.EXECUTED
    assert prep.approved_by == "admin_1"
    assert prep.approval_role == UserRole.EXAM_ADMIN
    assert prep.approved_at is not None

    assert len(backend.evaluation_history) == 1
    assert (
        backend.evaluation_history[0]["action"]
        == "MERIT_LIST_PUBLISHED"
    )


def test_merit_list_rejects_invalid_token_without_approval(backend):
    prep = backend.prepare_merit_list_publication(
        exam_id=backend.exam_id,
        version_tag="v1.0"
    )

    with pytest.raises(PermissionError):
        backend.publish_merit_list(
            preparation_id=prep.preparation_id,
            approver_token="invalid-token",
            user_role=UserRole.EXAM_ADMIN,
            approver_id="admin_1"
        )

    assert prep.status == PreparationStatus.PENDING_APPROVAL
    assert prep.approved_by is None
    assert prep.approval_role is None
    assert prep.approved_at is None
    assert backend.evaluation_history == []


def test_merit_list_cannot_be_published_twice(backend):
    prep = backend.prepare_merit_list_publication(
        exam_id=backend.exam_id,
        version_tag="v1.0"
    )

    backend.publish_merit_list(
        preparation_id=prep.preparation_id,
        approver_token=prep.approver_token,
        user_role=UserRole.EXAM_ADMIN,
        approver_id="admin_1"
    )

    with pytest.raises(PermissionError):
        backend.publish_merit_list(
            preparation_id=prep.preparation_id,
            approver_token=prep.approver_token,
            user_role=UserRole.EXAM_ADMIN,
            approver_id="admin_1"
        )

    assert len(backend.evaluation_history) == 1


def test_answer_key_update_rolls_back_on_recalculation_failure(
    backend,
    monkeypatch
):
    prep = backend.prepare_answer_key_update(
        exam_id=backend.exam_id,
        shift_id="SHIFT-1",
        question_id="Q1",
        proposed_action="CHANGE_OPTION",
        new_correct_options=["C"],
        reason="Regression test"
    )

    original_answer_keys = copy.deepcopy(backend.answer_keys)
    original_candidates = copy.deepcopy(backend.candidates)
    original_shift_stats = copy.deepcopy(backend.shift_stats)
    original_result_version = backend.result_version
    original_history = copy.deepcopy(backend.evaluation_history)

    original_normalisation = backend._apply_shift_normalisation

    def fail_after_normalisation():
        original_normalisation()
        raise RuntimeError("Simulated recalculation failure")

    monkeypatch.setattr(
        backend,
        "_apply_shift_normalisation",
        fail_after_normalisation
    )

    with pytest.raises(RuntimeError, match="Simulated recalculation failure"):
        backend.approve_answer_key_change(
            preparation_id=prep.preparation_id,
            approver_token=prep.approver_token,
            user_role=UserRole.EXAM_ADMIN,
            approver_id="admin_1"
        )

    assert backend.answer_keys == original_answer_keys
    assert backend.candidates == original_candidates
    assert backend.shift_stats == original_shift_stats
    assert backend.result_version == original_result_version
    assert backend.evaluation_history == original_history

    assert prep.status == PreparationStatus.PENDING_APPROVAL
    assert prep.approved_by is None
    assert prep.approval_role is None
    assert prep.approved_at is None
