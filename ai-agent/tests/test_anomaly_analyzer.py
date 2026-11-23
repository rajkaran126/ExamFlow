
from app.models import (
    AnomalyClassification,
    CandidateScorecard,
    QualificationStatus,
    ShiftStatistics,
)
from app.services.anomaly_analyzer import AnomalyAnalyzer


def make_shift(shift_id, rate, appeared=100, qualified=50):
    return ShiftStatistics(
        exam_id="EXAM-2026",
        shift_id=shift_id,
        total_registered=120,
        total_appeared=appeared,
        mean_raw_score=50.0,
        std_dev_raw_score=10.0,
        min_score=0.0,
        max_score=100.0,
        total_qualified=qualified,
        qualification_rate_percent=rate,
        sectional_failure_counts={},
        minimum_attempt_failure_count=0,
        proctoring_disqualification_count=0,
    )


def test_missing_answer_key_entries_are_detected():
    analyzer = AnomalyAnalyzer()

    reports = analyzer.analyze_answer_key(
        ["Q1", "Q2", "Q3"],
        ["Q1", "Q3"],
    )

    assert len(reports) == 1
    assert reports[0].classification == AnomalyClassification.CONFIRMED_ISSUE
    assert reports[0].evidence["missing_question_ids"] == ["Q2"]


def test_duplicate_answer_key_entries_are_detected():
    analyzer = AnomalyAnalyzer()

    reports = analyzer.analyze_answer_key(
        ["Q1", "Q2"],
        ["Q1", "Q1", "Q2"],
    )

    assert any(
        report.title == "Duplicate answer-key entries"
        for report in reports
    )


def test_unexpected_answer_key_entries_are_reported():
    analyzer = AnomalyAnalyzer()

    reports = analyzer.analyze_answer_key(
        ["Q1", "Q2"],
        ["Q1", "Q3"],
    )

    assert any(
        report.title == "Unexpected answer-key entries"
        for report in reports
    )


def test_duplicate_question_identifiers_are_detected():
    reports = AnomalyAnalyzer().analyze_duplicate_questions(
        ["Q1", "Q2", "Q1"]
    )

    assert len(reports) == 1
    assert reports[0].evidence["duplicate_identifiers"]["Q1"] == 2


def test_unique_question_identifiers_produce_no_anomaly():
    reports = AnomalyAnalyzer().analyze_duplicate_questions(
        ["Q1", "Q2", "Q3"]
    )

    assert reports == []


def test_invalid_shift_statistics_are_detected():
    shift = make_shift("SHIFT-1", 50, appeared=150, qualified=50)

    reports = AnomalyAnalyzer().analyze_shift_statistics([shift])

    assert any(
        report.classification == AnomalyClassification.CONFIRMED_ISSUE
        for report in reports
    )


def test_unusual_shift_rate_is_reported_as_possible():
    shifts = [
        make_shift("SHIFT-1", 40),
        make_shift("SHIFT-2", 42),
        make_shift("SHIFT-3", 90),
    ]

    reports = AnomalyAnalyzer().analyze_shift_statistics(shifts)

    assert any(
        report.classification == AnomalyClassification.POSSIBLE_ANOMALY
        and report.evidence["shift_id"] == "SHIFT-3"
        for report in reports
    )


def test_identical_shift_rates_do_not_create_outliers():
    shifts = [
        make_shift("SHIFT-1", 50),
        make_shift("SHIFT-2", 50),
        make_shift("SHIFT-3", 50),
    ]

    reports = AnomalyAnalyzer().analyze_shift_statistics(shifts)

    assert reports == []


def test_incomplete_question_extraction_is_unverified():
    reports = AnomalyAnalyzer().analyze_document_question_coverage(
        ["Q1", "Q2", "Q3"],
        ["Q1", "Q3"],
    )

    assert len(reports) == 1
    assert (
        reports[0].classification
        == AnomalyClassification.UNVERIFIED_OBSERVATION
    )


def test_complete_question_extraction_has_no_anomaly():
    reports = AnomalyAnalyzer().analyze_document_question_coverage(
        ["Q1", "Q2"],
        ["Q1", "Q2"],
    )

    assert reports == []


def test_scorecard_invalid_attempt_count_is_detected():
    card = CandidateScorecard(
        candidate_id="C001",
        candidate_name="Test Candidate",
        exam_id="EXAM-2026",
        shift_id="SHIFT-1",
        category="GEN",
        total_questions=50,
        attempted_questions=60,
        attempt_percentage=120,
        raw_score=70,
        sectional_scores={},
        negative_penalties=0,
        proctoring_deductions=0,
        normalized_score=70,
        sectional_cutoffs_cleared=True,
        minimum_attempts_cleared=True,
        proctoring_integrity_score=95,
        proctoring_disqualified=False,
        qualification_status=QualificationStatus.QUALIFIED,
    )

    reports = AnomalyAnalyzer().analyze_candidate_scorecards([card])

    assert len(reports) == 1
    assert "Attempted questions exceed total question count" in (
        reports[0].evidence["problems"]
    )
