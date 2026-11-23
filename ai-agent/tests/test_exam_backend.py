"""Automated Tests for PS-072 Examination Engine.
Tests negative marking, sectional cut-offs, minimum attempts, proctoring penalties,
disqualification, shift normalisation, and merit list tie-breakers.
"""

from app.services.exam_backend import exam_backend
from app.models import CandidateCategory, QualificationStatus

def test_negative_marking_and_sectional_cutoffs():
    # CAND-1001: High performer, cleared Section A and B
    sc = exam_backend.get_candidate_scorecard("CAND-1001")
    assert sc["raw_score"] == 85.5
    assert sc["sectional_scores"]["Section_A"] >= 3.5
    assert sc["sectional_scores"]["Section_B"] >= 25.0
    assert sc["sectional_cutoffs_cleared"] is True
    assert sc["qualification_status"] == "QUALIFIED"

def test_proctoring_critical_disqualification():
    # CAND-2002: Integrity score is 35.0% (<40%), must be DISQUALIFIED regardless of score
    sc = exam_backend.get_candidate_scorecard("CAND-2002")
    assert sc["proctoring_integrity_score"] < 40.0
    assert sc["proctoring_disqualified"] is True
    assert sc["qualification_status"] == "DISQUALIFIED"
    assert "Proctoring Malpractice" in sc["disqualification_reason"]

def test_minimum_attempts_failure():
    # CAND-2003: Attempted 18 questions (<20 required), must fail minimum attempts
    sc = exam_backend.get_candidate_scorecard("CAND-2003")
    assert sc["attempted_questions"] < 20
    assert sc["minimum_attempts_cleared"] is False
    assert sc["qualification_status"] == "NOT_QUALIFIED"
    assert "Minimum Attempts" in sc["disqualification_reason"]

def test_shift_normalisation_and_guards():
    # All non-disqualified candidates must have normalized scores between 0 and 100
    for cand_id in ["CAND-1001", "CAND-1002", "CAND-2001", "CAND-3001"]:
        sc = exam_backend.get_candidate_scorecard(cand_id)
        assert 0.0 <= sc["normalized_score"] <= 100.0

def test_dropped_questions_handling():
    # Shift 2 has Q42 dropped
    ak = exam_backend.get_answer_key("EXAM-2026-GATE", "SHIFT-2")
    assert "Q42" in ak["dropped_questions"]

def test_merit_list_tie_breaking():
    merit = exam_backend.get_merit_list("EXAM-2026-GATE")
    ranks = [c["rank"] for c in merit["merit_list"]]
    # Ranks must be contiguous starting from 1
    assert ranks == list(range(1, len(ranks) + 1))
    # Top rank should be highest normalized score
    assert merit["merit_list"][0]["normalized_score"] >= merit["merit_list"][1]["normalized_score"]
