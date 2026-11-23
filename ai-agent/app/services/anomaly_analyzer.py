
"""Evidence-based proactive anomaly analysis for EXAMFLOW AI.

Detects structural examination data issues and possible shift anomalies.
This module is read-only and never changes official examination results.
"""

from collections import Counter
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional, Sequence

from app.models import (
    AnomalyClassification,
    AnomalyReport,
    CandidateScorecard,
    ShiftStatistics,
)


class AnomalyAnalyzer:
    """Analyze supplied examination data without modifying official records."""

    def analyze_answer_key(
        self,
        expected_question_ids: Sequence[str],
        answer_key_question_ids: Sequence[str],
    ) -> List[AnomalyReport]:
        """Find missing and duplicate answer-key question identifiers."""

        expected = [str(item) for item in expected_question_ids]
        actual = [str(item) for item in answer_key_question_ids]

        expected_set = set(expected)
        actual_set = set(actual)

        missing = sorted(expected_set - actual_set)
        unexpected = sorted(actual_set - expected_set)

        counts = Counter(actual)
        duplicates = sorted(
            question_id
            for question_id, count in counts.items()
            if count > 1
        )

        reports = []

        if missing:
            reports.append(
                AnomalyReport(
                    classification=AnomalyClassification.CONFIRMED_ISSUE,
                    title="Missing answer-key entries",
                    description=(
                        "Some expected question identifiers are absent "
                        "from the supplied answer key."
                    ),
                    evidence={
                        "missing_question_ids": missing,
                        "expected_count": len(expected_set),
                        "answer_key_count": len(actual),
                    },
                    impact="Some questions may not have corresponding answer-key entries.",
                    recommended_action=(
                        "Verify the answer key against the approved "
                        "question paper before evaluation."
                    ),
                )
            )

        if duplicates:
            reports.append(
                AnomalyReport(
                    classification=AnomalyClassification.CONFIRMED_ISSUE,
                    title="Duplicate answer-key entries",
                    description=(
                        "Question identifiers occur more than once "
                        "in the supplied answer key."
                    ),
                    evidence={
                        "duplicate_question_ids": duplicates,
                        "duplicate_counts": {
                            item: counts[item] for item in duplicates
                        },
                    },
                    impact="Duplicate entries may cause ambiguous evaluation.",
                    recommended_action=(
                        "Review duplicate entries against the authoritative "
                        "approved answer key."
                    ),
                )
            )

        if unexpected:
            reports.append(
                AnomalyReport(
                    classification=AnomalyClassification.POSSIBLE_ANOMALY,
                    title="Unexpected answer-key entries",
                    description=(
                        "The answer key contains identifiers not present "
                        "in the supplied expected question list."
                    ),
                    evidence={
                        "unexpected_question_ids": unexpected,
                    },
                    impact="The answer key and expected question list may differ.",
                    recommended_action=(
                        "Check whether the question paper version and "
                        "answer key version match."
                    ),
                )
            )

        return reports

    def analyze_duplicate_questions(
        self,
        question_ids: Sequence[str],
    ) -> List[AnomalyReport]:
        """Detect repeated question identifiers."""

        identifiers = [str(item) for item in question_ids]
        counts = Counter(identifiers)

        duplicates = {
            identifier: count
            for identifier, count in counts.items()
            if count > 1
        }

        if not duplicates:
            return []

        return [
            AnomalyReport(
                classification=AnomalyClassification.POSSIBLE_ANOMALY,
                title="Repeated question identifiers",
                description=(
                    "The supplied question list contains repeated "
                    "identifiers. This does not establish that the "
                    "question content itself is duplicated."
                ),
                evidence={
                    "duplicate_identifiers": duplicates,
                    "total_identifiers": len(identifiers),
                },
                impact="Repeated identifiers may indicate a document or configuration issue.",
                recommended_action=(
                    "Compare the actual question content and source "
                    "document before making corrections."
                ),
            )
        ]

    def analyze_shift_statistics(
        self,
        shifts: Sequence[ShiftStatistics],
    ) -> List[AnomalyReport]:
        """Identify invalid statistics and possible inter-shift outliers."""

        if not shifts:
            return []

        reports = []

        # Structural validation: these conditions are objectively invalid.
        for shift in shifts:
            problems = []

            if shift.total_registered < 0:
                problems.append("Negative registered candidate count")

            if shift.total_appeared < 0:
                problems.append("Negative appeared candidate count")

            if shift.total_appeared > shift.total_registered:
                problems.append(
                    "Appeared candidates exceed registered candidates"
                )

            if shift.total_qualified < 0:
                problems.append("Negative qualified candidate count")

            if shift.total_qualified > shift.total_appeared:
                problems.append(
                    "Qualified candidates exceed appeared candidates"
                )

            if shift.std_dev_raw_score < 0:
                problems.append("Negative standard deviation")

            if shift.min_score > shift.max_score:
                problems.append("Minimum score exceeds maximum score")

            if not 0 <= shift.qualification_rate_percent <= 100:
                problems.append("Qualification rate is outside 0–100 percent")

            if problems:
                reports.append(
                    AnomalyReport(
                        classification=AnomalyClassification.CONFIRMED_ISSUE,
                        title=f"Invalid statistics: {shift.shift_id}",
                        description=(
                            "The supplied shift statistics violate "
                            "basic numerical consistency checks."
                        ),
                        evidence={
                            "exam_id": shift.exam_id,
                            "shift_id": shift.shift_id,
                            "problems": problems,
                        },
                        impact="These statistics should not be relied upon until verified.",
                        recommended_action=(
                            "Verify the source records and recompute "
                            "the affected statistics."
                        ),
                    )
                )

        # Possible outlier detection requires at least three shifts.
        valid_shifts = [
            shift for shift in shifts
            if (
                shift.total_registered >= 0
                and shift.total_appeared >= 0
                and shift.total_qualified >= 0
                and shift.total_qualified <= shift.total_appeared
                and 0 <= shift.qualification_rate_percent <= 100
            )
        ]

        if len(valid_shifts) < 3:
            return reports

        rates = [
            shift.qualification_rate_percent
            for shift in valid_shifts
        ]

        average_rate = mean(rates)
        deviation = pstdev(rates)

        # No statistical outlier claim when all rates are identical.
        if deviation == 0:
            return reports

        for shift in valid_shifts:
            difference = abs(
                shift.qualification_rate_percent - average_rate
            )

            z_score = difference / deviation

            if z_score >= 1.0:
                reports.append(
                    AnomalyReport(
                        classification=AnomalyClassification.POSSIBLE_ANOMALY,
                        title=f"Unusual qualification rate: {shift.shift_id}",
                        description=(
                            "This shift's qualification rate differs "
                            "substantially from the supplied shift group."
                        ),
                        evidence={
                            "exam_id": shift.exam_id,
                            "shift_id": shift.shift_id,
                            "shift_rate_percent": (
                                shift.qualification_rate_percent
                            ),
                            "group_average_percent": round(average_rate, 3),
                            "group_standard_deviation": round(deviation, 3),
                            "standardized_deviation": round(z_score, 3),
                            "shifts_compared": len(valid_shifts),
                        },
                        impact=(
                            "The difference may warrant investigation, "
                            "but does not establish an examination error."
                        ),
                        recommended_action=(
                            "Review shift difficulty, candidate distribution, "
                            "evaluation configuration and source statistics."
                        ),
                    )
                )

        return reports

    def analyze_candidate_scorecards(
        self,
        scorecards: Sequence[CandidateScorecard],
    ) -> List[AnomalyReport]:
        """Check scorecard fields for structural inconsistencies.

        This does not recalculate scores or determine qualification.
        """

        reports = []

        for card in scorecards:
            problems = []

            if card.total_questions < 0:
                problems.append("Negative total question count")

            if card.attempted_questions < 0:
                problems.append("Negative attempted question count")

            if card.attempted_questions > card.total_questions:
                problems.append(
                    "Attempted questions exceed total question count"                )

            if not 0 <= card.attempt_percentage <= 100:
                problems.append("Attempt percentage outside 0–100")

            if card.proctoring_integrity_score < 0 or (
                card.proctoring_integrity_score > 100
            ):
                problems.append(
                    "Proctoring integrity score outside 0–100"
                )

            if card.qualification_status.value == "DISQUALIFIED":
                if not card.proctoring_disqualified and not card.disqualification_reason:
                    problems.append(
                        "Disqualified status has no supplied disqualification indicator or reason"
                    )

            if problems:
                reports.append(
                    AnomalyReport(
                        classification=AnomalyClassification.POSSIBLE_ANOMALY,
                        title=f"Scorecard consistency: {card.candidate_id}",
                        description=(
                            "The supplied candidate scorecard contains "
                            "fields requiring verification."
                        ),
                        evidence={
                            "candidate_id": card.candidate_id,
                            "exam_id": card.exam_id,
                            "result_version": card.result_version,
                            "problems": problems,
                        },
                        impact=(
                            "The scorecard may contain inconsistent "
                            "or incomplete information."
                        ),
                        recommended_action=(
                            "Verify the scorecard against authoritative "
                            "evaluation and proctoring records."
                        ),
                    )
                )

        return reports

    def analyze_document_question_coverage(
        self,
        expected_question_ids: Sequence[str],
        document_question_ids: Sequence[str],
    ) -> List[AnomalyReport]:
        """Compare expected question IDs with extracted document IDs."""

        expected = set(map(str, expected_question_ids))
        extracted = set(map(str, document_question_ids))

        missing = sorted(expected - extracted)

        if not missing:
            return []

        return [
            AnomalyReport(
                classification=AnomalyClassification.UNVERIFIED_OBSERVATION,
                title="Question extraction coverage gap",
                description=(
                    "Some expected question identifiers were not found "
                    "in the extracted document data. OCR or extraction "
                    "failure may explain the difference."
                ),
                evidence={
                    "missing_identifiers": missing,
                    "expected_count": len(expected),
                    "extracted_count": len(extracted),
                },
                impact="The extracted document may be incomplete.",
                recommended_action=(
                    "Inspect the original PDF pages and OCR results "
                    "before concluding that questions are missing."
                ),
            )
        ]


anomaly_analyzer = AnomalyAnalyzer()
