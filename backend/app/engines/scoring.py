"""Deterministic Scoring Engine (Rule 1, Rule 2, Rule 4, Rule 12)."""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from app.engines.enums import ResponseStatus, DroppedQuestionScoringRule
from app.engines.exceptions import ScoringError

DECISION_LOG = [
    {
        "id": "DL-006",
        "rule": "Rule 1 - Multiple Correct Options",
        "description": "Candidate must select all correct options to be awarded full marks. Partial credit is not awarded unless explicitly configured."
    }
]


@dataclass
class SectionScoreResult:
    section_id: str
    section_name: str
    total_questions: int
    attempted: int
    correct_count: int
    wrong_count: int
    not_attempted_count: int
    raw_section_score: Decimal
    cut_off_applied: Decimal
    qualified: bool
    disqualification_reason: Optional[str] = None


@dataclass
class CandidateRawScoreResult:
    candidate_id: str
    total_questions: int
    attempted_questions: int
    correct_answers: int
    incorrect_answers: int
    total_positive_marks: Decimal
    total_negative_marks: Decimal
    raw_score: Decimal
    section_results: list[SectionScoreResult] = field(default_factory=list)


def evaluate_question(
    response_status: str,
    selected_option: Optional[str],
    is_late: bool,
    correct_options: list[str],
    marks_per_correct: Decimal,
    negative_marks_per_wrong: Decimal,
    dropped_rule: Optional[str] = None,
) -> tuple[Decimal, str]:
    """
    Evaluates a single question response according to PS-072 rules.
    Returns: (marks_awarded, evaluation_code: 'CORRECT' | 'WRONG' | 'NOT_ATTEMPTED' | 'DROPPED')
    """
    # Rule 4: Late section responses become not attempted and receive no penalty
    if is_late:
        return Decimal('0.00'), 'NOT_ATTEMPTED'

    # Rule 2: Dropped question handling
    if dropped_rule:
        if dropped_rule == DroppedQuestionScoringRule.AWARD_ALL.value:
            return marks_per_correct, 'DROPPED'
        elif dropped_rule == DroppedQuestionScoringRule.AWARD_NONE.value:
            return Decimal('0.00'), 'DROPPED'
        elif dropped_rule == DroppedQuestionScoringRule.AWARD_CORRECT_ONLY.value:
            # Fall through to standard scoring
            pass

    # Rule 6 / Section 6: A marked-for-review response without a selected option must not be treated as a valid answer
    if response_status == ResponseStatus.MARKED_FOR_REVIEW.value and not selected_option:
        return Decimal('0.00'), 'NOT_ATTEMPTED'

    # Not attempted questions receive no negative penalty
    if response_status == ResponseStatus.NOT_ATTEMPTED.value or not selected_option:
        return Decimal('0.00'), 'NOT_ATTEMPTED'

    # Parse candidate chosen options (support comma-separated for multi-correct)
    chosen_set = {opt.strip().upper() for opt in selected_option.split(',') if opt.strip()}
    correct_set = {opt.strip().upper() for opt in correct_options if opt.strip()}

    if chosen_set == correct_set:
        return marks_per_correct, 'CORRECT'
    else:
        # Penalty for wrong answer (Rule 1)
        return -abs(negative_marks_per_wrong), 'WRONG'


def score_candidate_responses(
    candidate_id: str,
    responses: list[dict],
    sections_config: list[dict],
    answer_keys: dict[str, list[str]], # key: question_id -> correct_options
    dropped_questions: dict[str, str], # key: question_id -> scoring_rule
) -> CandidateRawScoreResult:
    """
    Computes deterministic section and raw scores for a candidate.
    Uses Decimal throughout to prevent floating point drift (Rule 12).
    """
    responses_by_section: dict[str, list[dict]] = {}
    for r in responses:
        sec_id = str(r["section_id"])
        responses_by_section.setdefault(sec_id, []).append(r)

    total_exam_questions = 0
    total_attempted = 0
    total_correct = 0
    total_wrong = 0
    total_positive = Decimal('0.0000')
    total_negative = Decimal('0.0000')
    
    section_results: list[SectionScoreResult] = []

    for sec in sections_config:
        sec_id = str(sec["id"])
        sec_name = sec.get("name", f"Section {sec_id}")
        q_count = sec.get("question_count", 0)
        total_exam_questions += q_count
        
        marks_correct = Decimal(str(sec.get("marks_per_correct", "1.00")))
        marks_wrong = Decimal(str(sec.get("negative_marks_per_wrong", "0.25")))
        raw_cut_off = Decimal(str(sec.get("cut_off_raw", "0.00")))

        sec_responses = responses_by_section.get(sec_id, [])
        sec_correct = 0
        sec_wrong = 0
        sec_not_att = 0
        sec_raw_score = Decimal('0.0000')

        # Rule 4: If an entire section was skipped / zero responses, it's treated as skipped
        for resp in sec_responses:
            qid = str(resp["question_id"])
            correct_opts = answer_keys.get(qid, [])
            dropped_rule = dropped_questions.get(qid)
            
            score_delta, eval_code = evaluate_question(
                response_status=resp.get("status", ResponseStatus.NOT_ATTEMPTED.value),
                selected_option=resp.get("selected_option"),
                is_late=resp.get("is_late", False),
                correct_options=correct_opts,
                marks_per_correct=marks_correct,
                negative_marks_per_wrong=marks_wrong,
                dropped_rule=dropped_rule
            )

            if eval_code == 'CORRECT':
                sec_correct += 1
                total_positive += score_delta
                sec_raw_score += score_delta
            elif eval_code == 'WRONG':
                sec_wrong += 1
                total_negative += abs(score_delta)
                sec_raw_score += score_delta
            elif eval_code == 'DROPPED':
                if score_delta > 0:
                    sec_correct += 1
                    total_positive += score_delta
                    sec_raw_score += score_delta
                else:
                    sec_not_att += 1
            else: # NOT_ATTEMPTED
                sec_not_att += 1

        sec_attempted = sec_correct + sec_wrong
        total_attempted += sec_attempted
        total_correct += sec_correct
        total_wrong += sec_wrong

        # Missing questions not present in responses are counted as not attempted
        unrecorded_q = max(0, q_count - len(sec_responses))
        sec_not_att += unrecorded_q

        section_results.append(SectionScoreResult(
            section_id=sec_id,
            section_name=sec_name,
            total_questions=q_count,
            attempted=sec_attempted,
            correct_count=sec_correct,
            wrong_count=sec_wrong,
            not_attempted_count=sec_not_att,
            raw_section_score=sec_raw_score,
            cut_off_applied=raw_cut_off,
            qualified=sec_raw_score >= raw_cut_off
        ))

    overall_raw = total_positive - total_negative

    return CandidateRawScoreResult(
        candidate_id=candidate_id,
        total_questions=total_exam_questions,
        attempted_questions=total_attempted,
        correct_answers=total_correct,
        incorrect_answers=total_wrong,
        total_positive_marks=total_positive,
        total_negative_marks=total_negative,
        raw_score=overall_raw,
        section_results=section_results
    )
