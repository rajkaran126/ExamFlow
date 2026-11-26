"""Re-Evaluation Engine (Rule 11)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.engines.exceptions import ReEvaluationError


@dataclass
class ReEvaluationResult:
    candidate_id: str
    original_marks: Decimal
    revised_marks: Decimal
    marks_changed: bool
    new_version: int
    audit_notes: str


def check_and_execute_re_evaluation(
    candidate_id: str,
    current_version: int,
    has_prior_completed_request: bool,
    current_score: Decimal,
    new_calculated_score: Decimal,
    reason: str,
    initiating_admin: str
) -> ReEvaluationResult:
    """
    Rule 11 – Re-evaluation:
    - Allow only ONE re-evaluation per candidate.
    - Increment result version.
    - Preserve previous result and audit trail.
    - Re-evaluation is strictly transactional.
    """
    if has_prior_completed_request:
        raise ReEvaluationError(
            f"Rule 11 Violation: Candidate '{candidate_id}' has already undergone re-evaluation. A second re-evaluation attempt is strictly prohibited."
        )

    new_version = current_version + 1
    marks_diff = new_calculated_score - current_score
    changed = marks_diff != Decimal('0.00')

    notes = (
        f"Re-evaluation executed by {initiating_admin}. "
        f"Version incremented from {current_version} to {new_version}. "
        f"Original marks: {current_score:.4f}, Revised marks: {new_calculated_score:.4f} (Delta: {marks_diff:+.4f}). "
        f"Reason: {reason}"
    )

    return ReEvaluationResult(
        candidate_id=candidate_id,
        original_marks=current_score,
        revised_marks=new_calculated_score,
        marks_changed=changed,
        new_version=new_version,
        audit_notes=notes
    )
