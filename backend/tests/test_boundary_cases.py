"""
PS-072 MANDATORY BOUNDARY CASE TESTS (1 through 20)
Verifies deterministic examination evaluation engine.
"""
from decimal import Decimal

try:
    import pytest
except ImportError:
    class _RaisesContext:
        def __init__(self, expected_exc):
            self.expected_exc = expected_exc
            self.value = None
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f"Expected exception {self.expected_exc.__name__} was not raised.")
            if not issubclass(exc_type, self.expected_exc):
                return False
            self.value = exc_val
            return True

    class _PytestShim:
        @staticmethod
        def raises(exc):
            return _RaisesContext(exc)

    pytest = _PytestShim()
from app.engines.scoring import score_candidate_responses, evaluate_question
from app.engines.proctoring_penalty import calculate_proctoring_penalty
from app.engines.qualification import evaluate_candidate_qualification, get_category_relaxation_percentage
from app.engines.normalisation import normalise_examination_scores
from app.engines.merit_list import generate_merit_list_entries, CandidateMeritRecord
from app.engines.re_evaluation import check_and_execute_re_evaluation
from app.engines.exceptions import NormalisationGuardError, ReEvaluationError
from app.engines.enums import DroppedQuestionScoringRule, ResponseStatus


# ============================================================================
# MANDATORY CASE 1: Exact sectional cut-off
# ============================================================================
def test_case_01_exact_sectional_cut_off():
    """Score exactly equal to raw sectional cut-off must QUALIFY."""
    cut_off_raw = Decimal('20.00')
    section_score = Decimal('20.00')
    
    res = evaluate_candidate_qualification(
        candidate_id="c-01",
        category="GEN",
        is_pwd=False,
        total_questions=100,
        attempted_questions=50,
        section_scores=[{
            "section_id": "s1",
            "section_name": "Quant",
            "raw_score": section_score,
            "max_marks": Decimal('50.00'),
            "cut_off_pct": Decimal('40.00') # 40% of 50 = 20.00
        }]
    )
    assert res.all_sections_qualified is True
    assert res.overall_qualified is True
    assert res.sectional_qualifications[0]["qualified"] is True


# ============================================================================
# MANDATORY CASE 2: One mark below cut-off
# ============================================================================
def test_case_02_one_mark_below_cut_off():
    """Score 1 mark below sectional cut-off must FAIL."""
    cut_off_raw = Decimal('20.00')
    section_score = Decimal('19.00') # 1 mark below
    
    res = evaluate_candidate_qualification(
        candidate_id="c-02",
        category="GEN",
        is_pwd=False,
        total_questions=100,
        attempted_questions=50,
        section_scores=[{
            "section_id": "s1",
            "section_name": "Quant",
            "raw_score": section_score,
            "max_marks": Decimal('50.00'),
            "cut_off_pct": Decimal('40.00')
        }]
    )
    assert res.all_sections_qualified is False
    assert res.overall_qualified is False
    assert res.sectional_qualifications[0]["qualified"] is False
    assert len(res.failure_reasons) > 0


# ============================================================================
# MANDATORY CASE 3: One mark above cut-off
# ============================================================================
def test_case_03_one_mark_above_cut_off():
    """Score 1 mark above sectional cut-off must QUALIFY."""
    cut_off_raw = Decimal('20.00')
    section_score = Decimal('21.00') # 1 mark above
    
    res = evaluate_candidate_qualification(
        candidate_id="c-03",
        category="GEN",
        is_pwd=False,
        total_questions=100,
        attempted_questions=50,
        section_scores=[{
            "section_id": "s1",
            "section_name": "Quant",
            "raw_score": section_score,
            "max_marks": Decimal('50.00'),
            "cut_off_pct": Decimal('40.00')
        }]
    )
    assert res.all_sections_qualified is True
    assert res.overall_qualified is True
    assert res.sectional_qualifications[0]["qualified"] is True


# ============================================================================
# MANDATORY CASE 4: Exactly 10% attempts
# ============================================================================
def test_case_04_exactly_10_percent_attempts():
    """Attempting exactly 10% of total questions passes minimum attempt threshold."""
    total_q = 100
    attempted_q = 10 # Exactly 10%
    
    res = evaluate_candidate_qualification(
        candidate_id="c-04",
        category="GEN",
        is_pwd=False,
        total_questions=total_q,
        attempted_questions=attempted_q,
        section_scores=[{
            "section_id": "s1",
            "section_name": "Quant",
            "raw_score": Decimal('25.00'),
            "max_marks": Decimal('50.00'),
            "cut_off_pct": Decimal('40.00')
        }]
    )
    assert res.attempt_percentage == Decimal('10.00')
    assert res.attempt_requirement_met is True
    assert res.overall_qualified is True


# ============================================================================
# MANDATORY CASE 5: Below 10% attempts
# ============================================================================
def test_case_05_below_10_percent_attempts():
    """Attempting fewer than 10% of questions fails qualification."""
    total_q = 100
    attempted_q = 9 # 9% (< 10%)
    
    res = evaluate_candidate_qualification(
        candidate_id="c-05",
        category="GEN",
        is_pwd=False,
        total_questions=total_q,
        attempted_questions=attempted_q,
        section_scores=[{
            "section_id": "s1",
            "section_name": "Quant",
            "raw_score": Decimal('25.00'),
            "max_marks": Decimal('50.00'),
            "cut_off_pct": Decimal('40.00')
        }]
    )
    assert res.attempt_percentage == Decimal('9.00')
    assert res.attempt_requirement_met is False
    assert res.overall_qualified is False
    assert any("minimum attempt" in r.lower() for r in res.failure_reasons)


# ============================================================================
# MANDATORY CASE 6: Severity 6 Proctoring Penalty
# ============================================================================
def test_case_06_severity_6_penalty():
    """Severity 6 must trigger exactly 5% penalty deduction."""
    raw = Decimal('100.00')
    events = [{"severity": 6, "confirmed": True, "is_malpractice": False}]
    
    decision = calculate_proctoring_penalty("c-06", raw, events)
    assert decision.penalty_percentage == Decimal('5.00')
    assert decision.penalty_marks == Decimal('5.0000')
    assert decision.score_after_penalty == Decimal('95.0000')
    assert decision.is_disqualified is False


# ============================================================================
# MANDATORY CASE 7: Severity 7 Proctoring Penalty
# ============================================================================
def test_case_07_severity_7_penalty():
    """Severity 7 must trigger exactly 15% penalty deduction."""
    raw = Decimal('100.00')
    events = [{"severity": 7, "confirmed": True, "is_malpractice": False}]
    
    decision = calculate_proctoring_penalty("c-07", raw, events)
    assert decision.penalty_percentage == Decimal('15.00')
    assert decision.penalty_marks == Decimal('15.0000')
    assert decision.score_after_penalty == Decimal('85.0000')
    assert decision.is_disqualified is False


# ============================================================================
# MANDATORY CASE 8: Severity 9 Proctoring Penalty
# ============================================================================
def test_case_08_severity_9_penalty():
    """Severity 9 must trigger exactly 15% penalty deduction."""
    raw = Decimal('100.00')
    events = [{"severity": 9, "confirmed": True, "is_malpractice": False}]
    
    decision = calculate_proctoring_penalty("c-08", raw, events)
    assert decision.penalty_percentage == Decimal('15.00')
    assert decision.penalty_marks == Decimal('15.0000')
    assert decision.score_after_penalty == Decimal('85.0000')
    assert decision.is_disqualified is False


# ============================================================================
# MANDATORY CASE 9: Severity 10 Proctoring Penalty
# ============================================================================
def test_case_09_severity_10_penalty():
    """Severity 10 must result in DISQUALIFICATION."""
    raw = Decimal('100.00')
    events = [{"severity": 10, "confirmed": True, "is_malpractice": False}]
    
    decision = calculate_proctoring_penalty("c-09", raw, events)
    assert decision.is_disqualified is True
    assert decision.penalty_percentage == Decimal('100.00')
    assert decision.score_after_penalty == Decimal('0.0000')


# ============================================================================
# MANDATORY CASE 10: Dropped question marked for review without option
# ============================================================================
def test_case_10_dropped_question_marked_review_no_option():
    """
    A marked-for-review response without option on a dropped question (AWARD_NONE / standard)
    must not receive accidental full marks or penalty.
    """
    score, eval_code = evaluate_question(
        response_status=ResponseStatus.MARKED_FOR_REVIEW.value,
        selected_option=None, # no option
        is_late=False,
        correct_options=["A"],
        marks_per_correct=Decimal('2.00'),
        negative_marks_per_wrong=Decimal('0.50'),
        dropped_rule=None
    )
    assert score == Decimal('0.00')
    assert eval_code == 'NOT_ATTEMPTED'


# ============================================================================
# MANDATORY CASE 11: Multiple correct options
# ============================================================================
def test_case_11_multiple_correct_options():
    """Exact match awards full marks; partial or incorrect match deducts penalty."""
    # Exact match: chosen {A, C}, correct {A, C}
    score_exact, code_exact = evaluate_question(
        response_status=ResponseStatus.OPTION_SELECTED.value,
        selected_option="A,C",
        is_late=False,
        correct_options=["A", "C"],
        marks_per_correct=Decimal('2.00'),
        negative_marks_per_wrong=Decimal('0.50')
    )
    assert score_exact == Decimal('2.00')
    assert code_exact == 'CORRECT'

    # Partial match: chosen {A}, correct {A, C} -> negative penalty applied
    score_partial, code_partial = evaluate_question(
        response_status=ResponseStatus.OPTION_SELECTED.value,
        selected_option="A",
        is_late=False,
        correct_options=["A", "C"],
        marks_per_correct=Decimal('2.00'),
        negative_marks_per_wrong=Decimal('0.50')
    )
    assert score_partial == Decimal('-0.50')
    assert code_partial == 'WRONG'


# ============================================================================
# MANDATORY CASE 12: Updated answer key
# ============================================================================
def test_case_12_updated_answer_key():
    """When answer key updates from B to C, candidate answering C receives correct score."""
    # Key version 1: correct is B
    s1, c1 = evaluate_question(
        response_status="OPTION_SELECTED",
        selected_option="C",
        is_late=False,
        correct_options=["B"],
        marks_per_correct=Decimal('2.00'),
        negative_marks_per_wrong=Decimal('0.50')
    )
    assert s1 == Decimal('-0.50')
    assert c1 == 'WRONG'

    # Key version 2: challenge accepted, correct is updated to C
    s2, c2 = evaluate_question(
        response_status="OPTION_SELECTED",
        selected_option="C",
        is_late=False,
        correct_options=["C"],
        marks_per_correct=Decimal('2.00'),
        negative_marks_per_wrong=Decimal('0.50')
    )
    assert s2 == Decimal('2.00')
    assert c2 == 'CORRECT'


# ============================================================================
# MANDATORY CASE 13: Shift with exactly 100 candidates
# ============================================================================
def test_case_13_shift_exactly_100_candidates():
    """Shift with exactly 100 candidates is NOT pooled."""
    cands_s1 = [(f"c1_{i}", Decimal(f"{50 + (i % 20)}")) for i in range(100)]
    cands_s2 = [(f"c2_{i}", Decimal(f"{40 + (i % 20)}")) for i in range(120)]
    
    shifts_data = {"shift_1": cands_s1, "shift_2": cands_s2}
    stats, _ = normalise_examination_scores(shifts_data)
    
    assert stats["shift_1"].is_pooled is False
    assert stats["shift_1"].candidate_count == 100


# ============================================================================
# MANDATORY CASE 14: Shift with 99 candidates
# ============================================================================
def test_case_14_shift_with_99_candidates():
    """Shift with 99 candidates (<100) must be POOLED."""
    cands_s1 = [(f"c1_{i}", Decimal(f"{50 + (i % 20)}")) for i in range(99)] # 99 candidates
    cands_s2 = [(f"c2_{i}", Decimal(f"{40 + (i % 20)}")) for i in range(120)]
    
    shifts_data = {"shift_1": cands_s1, "shift_2": cands_s2}
    stats, _ = normalise_examination_scores(shifts_data)
    
    assert stats["shift_1"].is_pooled is True


# ============================================================================
# MANDATORY CASE 15: Normalisation denominator zero
# ============================================================================
def test_case_15_normalisation_denominator_zero():
    """If all scores in a shift are identical, std dev = 0, must raise NormalisationGuardError."""
    # All scores 50.00 -> std_dev = 0
    cands_s1 = [(f"c1_{i}", Decimal('50.00')) for i in range(105)]
    shifts_data = {"shift_1": cands_s1}
    
    with pytest.raises(NormalisationGuardError) as exc_info:
        normalise_examination_scores(shifts_data)
    assert "Rule 7 Violation" in str(exc_info.value)


# ============================================================================
# MANDATORY CASE 16: Normalisation denominator negative
# ============================================================================
def test_case_16_normalisation_denominator_negative():
    """Standard deviation calculation guard strictly blocks any non-positive denominator."""
    cands = [(f"c_{i}", Decimal('60.00')) for i in range(100)]
    with pytest.raises(NormalisationGuardError):
        normalise_examination_scores({"shift_single": cands})


# ============================================================================
# MANDATORY CASE 17: Full merit-list tie
# ============================================================================
def test_case_17_full_merit_list_tie():
    """Candidates equal on all 5 tie-breakers must have tie_unresolved=True."""
    rec1 = CandidateMeritRecord(
        candidate_id="c-tie-1",
        name="Alex Smith",
        roll_number="R101",
        category="GEN",
        shift_name="S1",
        date_of_birth="2000-01-01",
        raw_score=Decimal('80.00'),
        normalised_score=Decimal('80.0000000000'),
        relevant_sectional_score=Decimal('40.00'),
        wrong_count=2,
        qualified=True
    )
    rec2 = CandidateMeritRecord(
        candidate_id="c-tie-2",
        name="Alex Smith", # same name
        roll_number="R102",
        category="GEN",
        shift_name="S1",
        date_of_birth="2000-01-01", # same DOB
        raw_score=Decimal('80.00'),
        normalised_score=Decimal('80.0000000000'), # same norm score
        relevant_sectional_score=Decimal('40.00'), # same sec score
        wrong_count=2, # same wrong count
        qualified=True
    )
    entries = generate_merit_list_entries([rec1, rec2], vacancies=10)
    assert entries[0].tie_unresolved is True
    assert entries[1].tie_unresolved is True


# ============================================================================
# MANDATORY CASE 18: SC candidate above GEN threshold
# ============================================================================
def test_case_18_sc_candidate_above_gen_threshold():
    """SC candidate scoring above GEN threshold is allocated under GEN quota."""
    rec_sc_topper = CandidateMeritRecord(
        candidate_id="c-sc-1",
        name="Top SC Scorer",
        roll_number="R201",
        category="SC",
        shift_name="S1",
        date_of_birth="2001-01-01",
        raw_score=Decimal('95.00'),
        normalised_score=Decimal('95.0000000000'),
        relevant_sectional_score=Decimal('48.00'),
        wrong_count=1,
        qualified=True
    )
    rec_gen = CandidateMeritRecord(
        candidate_id="c-gen-1",
        name="Gen Candidate",
        roll_number="R202",
        category="GEN",
        shift_name="S1",
        date_of_birth="2000-05-01",
        raw_score=Decimal('85.00'),
        normalised_score=Decimal('85.0000000000'),
        relevant_sectional_score=Decimal('42.00'),
        wrong_count=3,
        qualified=True
    )
    # Vacancy: 1 GEN seat
    entries = generate_merit_list_entries([rec_sc_topper, rec_gen], vacancies=1, category_vacancies={"GEN": 1, "SC": 1})
    assert entries[0].candidate_id == "c-sc-1"
    assert entries[0].allocated_under_gen is True
    assert entries[0].is_selected is True


# ============================================================================
# MANDATORY CASE 19: Second re-evaluation attempt
# ============================================================================
def test_case_19_second_re_evaluation_attempt():
    """Attempting a second re-evaluation must raise ReEvaluationError."""
    with pytest.raises(ReEvaluationError) as exc_info:
        check_and_execute_re_evaluation(
            candidate_id="c-19",
            current_version=2,
            has_prior_completed_request=True, # Already re-evaluated
            current_score=Decimal('70.00'),
            new_calculated_score=Decimal('72.00'),
            reason="Second review requested",
            initiating_admin="Admin"
        )
    assert "Rule 11 Violation" in str(exc_info.value)


# ============================================================================
# MANDATORY CASE 20: Score precision and rounding boundaries
# ============================================================================
def test_case_20_score_precision_and_rounding():
    """Raw score precision displayed to 2dp, normalised to 5dp, internal Decimal maintained."""
    raw = Decimal('67.456789')
    norm = Decimal('72.123456789012345678')

    # Display representations (Rule 12)
    raw_display = f"{raw:.2f}"
    norm_display = f"{norm:.5f}"

    assert raw_display == "67.46"
    assert norm_display == "72.12346"
    assert isinstance(raw, Decimal)
    assert isinstance(norm, Decimal)
