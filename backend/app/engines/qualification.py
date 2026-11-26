"""Qualification Engine (Rule 3, Rule 4, Rule 8, Rule 12)."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from app.engines.enums import QualificationStatus, CandidateCategory


@dataclass
class QualificationDecisionResult:
    candidate_id: str
    attempt_percentage: Decimal
    attempt_requirement_met: bool
    sectional_qualifications: list[dict] # {section_id, raw_score, cut_off, qualified, reason}
    all_sections_qualified: bool
    overall_qualified: bool
    final_status: str
    failure_reasons: list[str] = field(default_factory=list)


def get_category_relaxation_percentage(category: str, is_pwd: bool) -> Decimal:
    """
    Rule 3 – Category relaxation:
    - OBC/EWS: 5 percentage points.
    - SC/ST: 10 percentage points.
    - PwD: additional 5 percentage points.
    """
    cat = category.strip().upper()
    relaxation = Decimal('0.00')

    if cat in [CandidateCategory.OBC.value, CandidateCategory.EWS.value]:
        relaxation += Decimal('5.00')
    elif cat in [CandidateCategory.SC.value, CandidateCategory.ST.value]:
        relaxation += Decimal('10.00')

    if is_pwd:
        relaxation += Decimal('5.00')

    return relaxation


def evaluate_candidate_qualification(
    candidate_id: str,
    category: str,
    is_pwd: bool,
    total_questions: int,
    attempted_questions: int,
    section_scores: list[dict], # {section_id, section_name, raw_score, max_marks, cut_off_pct, cut_off_raw}
    is_disqualified: bool = False,
    disqualification_reason: Optional[str] = None
) -> QualificationDecisionResult:
    """
    Determines overall qualification according to PS-072 rules.
    """
    failure_reasons = []

    # Check Proctoring Disqualification
    if is_disqualified:
        failure_reasons.append(disqualification_reason or "Disqualified due to proctoring violation.")
        return QualificationDecisionResult(
            candidate_id=candidate_id,
            attempt_percentage=Decimal('0.00'),
            attempt_requirement_met=False,
            sectional_qualifications=[],
            all_sections_qualified=False,
            overall_qualified=False,
            final_status=QualificationStatus.DISQUALIFIED.value,
            failure_reasons=failure_reasons
        )

    # Rule 8 – Minimum attempts:
    # Candidates attempting fewer than 10% of the required questions fail.
    # Boundary: Exactly 10% passes minimum attempt requirement.
    if total_questions > 0:
        attempt_pct = (Decimal(attempted_questions) / Decimal(total_questions)) * Decimal('100.00')
    else:
        attempt_pct = Decimal('0.00')

    attempt_met = attempt_pct >= Decimal('10.00')
    if not attempt_met:
        failure_reasons.append(
            f"Failed minimum attempt threshold: attempted {attempted_questions}/{total_questions} ({attempt_pct:.2f}%), required >= 10.00%"
        )

    # Rule 3 & Sectional Cut-offs
    relaxation_pp = get_category_relaxation_percentage(category, is_pwd)
    sectional_qualifications = []
    all_sec_qualified = True

    for sec in section_scores:
        sec_id = str(sec["section_id"])
        sec_name = sec.get("section_name", sec_id)
        raw_score = Decimal(str(sec["raw_score"]))
        max_marks = Decimal(str(sec.get("max_marks", "100.00")))
        base_cutoff_pct = Decimal(str(sec.get("cut_off_pct", "40.00")))

        # Effective cutoff percentage after category relaxation
        effective_cutoff_pct = max(Decimal('0.00'), base_cutoff_pct - relaxation_pp)
        # Compute exact raw cut-off
        effective_raw_cutoff = (effective_cutoff_pct / Decimal('100.00')) * max_marks

        # Compare using unrounded values (Rule 12)
        sec_passed = raw_score >= effective_raw_cutoff
        sec_reason = None
        if not sec_passed:
            all_sec_qualified = False
            sec_reason = f"Section '{sec_name}' score {raw_score:.2f} is below cut-off {effective_raw_cutoff:.2f} (relaxation applied: {relaxation_pp} pp)"
            failure_reasons.append(sec_reason)

        sectional_qualifications.append({
            "section_id": sec_id,
            "section_name": sec_name,
            "raw_score": raw_score,
            "effective_cut_off": effective_raw_cutoff,
            "effective_cut_off_pct": effective_cutoff_pct,
            "qualified": sec_passed,
            "reason": sec_reason
        })

    overall_qualified = attempt_met and all_sec_qualified
    final_status = QualificationStatus.QUALIFIED.value if overall_qualified else QualificationStatus.NOT_QUALIFIED.value

    return QualificationDecisionResult(
        candidate_id=candidate_id,
        attempt_percentage=attempt_pct,
        attempt_requirement_met=attempt_met,
        sectional_qualifications=sectional_qualifications,
        all_sections_qualified=all_sec_qualified,
        overall_qualified=overall_qualified,
        final_status=final_status,
        failure_reasons=failure_reasons
    )
