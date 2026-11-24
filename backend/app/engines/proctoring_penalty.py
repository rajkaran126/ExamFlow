"""Proctoring Penalty Engine (Rule 5)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

DECISION_LOG = [
    {
        "id": "DL-001",
        "rule": "Rule 5 – Proctoring Penalty Base",
        "description": "Proctoring penalty is calculated as a percentage deduction applied against the candidate's raw score. If score after penalty is negative, score is preserved as computed without clamping unless overall disqualified."
    }
]


@dataclass
class ProctoringPenaltyDecision:
    candidate_id: str
    max_severity: int
    is_malpractice: bool
    is_disqualified: bool
    penalty_percentage: Decimal
    penalty_marks: Decimal
    score_after_penalty: Decimal
    reason: Optional[str] = None


def calculate_proctoring_penalty(
    candidate_id: str,
    raw_score: Decimal,
    confirmed_events: list[dict], # list of dicts with 'severity', 'is_malpractice', 'confirmed'
) -> ProctoringPenaltyDecision:
    """
    Applies Rule 5:
    - Severity 4–6: 5% deduction.
    - Severity 7–9: 15% deduction.
    - Severity 10 or above: disqualification.
    - Confirmed malpractice: disqualification.
    """
    events = [e for e in confirmed_events if e.get("confirmed", True)]
    
    if not events:
        return ProctoringPenaltyDecision(
            candidate_id=candidate_id,
            max_severity=0,
            is_malpractice=False,
            is_disqualified=False,
            penalty_percentage=Decimal('0.00'),
            penalty_marks=Decimal('0.0000'),
            score_after_penalty=raw_score,
            reason=None
        )

    has_malpractice = any(e.get("is_malpractice", False) for e in events)
    max_sev = max(e.get("severity", 1) for e in events)

    # Disqualification check
    if has_malpractice or max_sev >= 10:
        penalty_pct = Decimal('100.00')
        reason = "Disqualified: Confirmed malpractice" if has_malpractice else f"Disqualified: Severity level {max_sev} reached or exceeded threshold (>=10)"
        return ProctoringPenaltyDecision(
            candidate_id=candidate_id,
            max_severity=max_sev,
            is_malpractice=has_malpractice,
            is_disqualified=True,
            penalty_percentage=penalty_pct,
            penalty_marks=raw_score,
            score_after_penalty=Decimal('0.0000'),
            reason=reason
        )

    # Deductions
    if 7 <= max_sev <= 9:
        penalty_pct = Decimal('15.00')
        reason = f"15% deduction applied due to severity level {max_sev} (range 7-9)"
    elif 4 <= max_sev <= 6:
        penalty_pct = Decimal('5.00')
        reason = f"5% deduction applied due to severity level {max_sev} (range 4-6)"
    else:
        # Severity 1-3
        penalty_pct = Decimal('0.00')
        reason = None

    penalty_marks = (raw_score * penalty_pct / Decimal('100.00'))
    score_after = raw_score - penalty_marks

    return ProctoringPenaltyDecision(
        candidate_id=candidate_id,
        max_severity=max_sev,
        is_malpractice=False,
        is_disqualified=False,
        penalty_percentage=penalty_pct,
        penalty_marks=penalty_marks,
        score_after_penalty=score_after,
        reason=reason
    )
