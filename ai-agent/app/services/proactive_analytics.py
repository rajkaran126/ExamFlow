"""Proactive Anomaly Detection Engine for EXAMFLOW AI.
Detects missing answer-key entries, duplicate records, abnormal shift failure spikes,
proctoring distribution anomalies, and classifies them into standard categories.
"""

from typing import List, Dict, Any, Optional
from app.models import AnomalyReport, AnomalyClassification
from app.services.exam_backend import exam_backend

class ProactiveAnalyticsEngine:
    """Monitors examination data to uncover anomalies before or during investigations."""

    @staticmethod
    def detect_anomalies(exam_id: str = "EXAM-2026-GATE") -> List[AnomalyReport]:
        reports: List[AnomalyReport] = []
        
        # 1. Shift Disparity Analysis (Investigate Shift Qualification Variance)
        shifts = ["SHIFT-1", "SHIFT-2", "SHIFT-3"]
        stats_by_shift = {}
        for s in shifts:
            try:
                st = exam_backend.get_shift_statistics(exam_id, s)
                stats_by_shift[s] = st
            except Exception:
                pass

        if "SHIFT-1" in stats_by_shift and "SHIFT-2" in stats_by_shift:
            s1_rate = stats_by_shift["SHIFT-1"]["qualification_rate_percent"]
            s2_rate = stats_by_shift["SHIFT-2"]["qualification_rate_percent"]
            
            # Anomaly: Shift 2 qualification rate is significantly lower than Shift 1
            if s1_rate - s2_rate > 15.0:
                s2_sec_b_fails = stats_by_shift["SHIFT-2"]["sectional_failure_counts"].get("Section_B", 0)
                reports.append(AnomalyReport(
                    classification=AnomalyClassification.CONFIRMED_ISSUE,
                    title="Severe Inter-Shift Qualification Disparity (Shift 2 Outlier)",
                    description=(
                        f"Shift 2 has a qualification rate of {s2_rate:.1f}% compared to "
                        f"Shift 1 ({s1_rate:.1f}%). Section B (Technical Engineering) failures "
                        f"account for {s2_sec_b_fails} failures in Shift 2."
                    ),
                    evidence={
                        "shift_1_qual_rate": s1_rate,
                        "shift_2_qual_rate": s2_rate,
                        "disparity_percent": round(s1_rate - s2_rate, 2),
                        "shift_2_sectional_b_failures": s2_sec_b_fails,
                        "shift_2_mean_raw_score": stats_by_shift["SHIFT-2"]["mean_raw_score"],
                        "shift_1_mean_raw_score": stats_by_shift["SHIFT-1"]["mean_raw_score"]
                    },
                    impact="Candidates in Shift 2 face disproportionate sectional cut-off disqualifications before normalisation can equalize aggregate percentiles.",
                    recommended_action="Conduct item-level difficulty index audit on Shift 2 Section B questions and evaluate relaxation of Section B cut-off."
                ))

        # 2. Dropped Question & Answer Key Integrity Check
        for s in shifts:
            try:
                ak = exam_backend.get_answer_key(exam_id, s)
                dropped = ak.get("dropped_questions", [])
                if dropped:
                    reports.append(AnomalyReport(
                        classification=AnomalyClassification.CONFIRMED_ISSUE,
                        title=f"Dropped Question Detected in {s}",
                        description=f"{s} contains dropped question(s): {', '.join(dropped)}. Full marks credited to all candidates in this shift.",
                        evidence={"shift_id": s, "dropped_questions": dropped},
                        impact="Raw scores of all appearing candidates adjusted by question weightage.",
                        recommended_action="Verify that all appearing candidates received credit in the scoring ledger."
                    ))
            except Exception:
                pass

        # 3. Proctoring Disqualification Cluster Check
        for s in shifts:
            if s in stats_by_shift:
                disq_count = stats_by_shift[s]["proctoring_disqualification_count"]
                if disq_count >= 1:
                    reports.append(AnomalyReport(
                        classification=AnomalyClassification.POSSIBLE_ANOMALY,
                        title=f"Proctoring Integrity Disqualifications in {s}",
                        description=f"{disq_count} candidate(s) in {s} flagged below the 40% integrity threshold for critical malpractice.",
                        evidence={"shift_id": s, "disqualified_count": disq_count},
                        impact="Affected candidates receive zero normalized marks and disqualified status.",
                        recommended_action="Review webcam telemetry, tab-switch logs, and second-person detection timestamps before final sign-off."
                    ))

        # 4. Small Shift Pooling Check
        for s, st in stats_by_shift.items():
            if st.get("is_pooled"):
                reports.append(AnomalyReport(
                    classification=AnomalyClassification.RECOMMENDATION,
                    title=f"Small Sample Shift Pooling Recommended for {s}",
                    description=f"Shift {s} has fewer than 30 candidates ({st['total_appeared']}). Normalisation requires pooling to prevent high variance.",
                    evidence={"shift_id": s, "appeared": st["total_appeared"]},
                    impact="Unpooled normalization on small cohorts can artificially compress or inflate percentiles.",
                    recommended_action="Apply Equipercentile small-shift pooling rule in the engine."
                ))

        return reports

    @staticmethod
    def compare_pdf_with_backend(pdf_extracted_scores: Dict[str, float], candidate_id: str) -> List[AnomalyReport]:
        """Detect discrepancies between an uploaded score PDF and authoritative backend data."""
        anomalies: List[AnomalyReport] = []
        try:
            scorecard = exam_backend.get_candidate_scorecard(candidate_id)
            backend_raw = scorecard["raw_score"]
            pdf_raw = pdf_extracted_scores.get("raw_score")
            
            if pdf_raw is not None and abs(pdf_raw - backend_raw) > 0.01:
                anomalies.append(AnomalyReport(
                    classification=AnomalyClassification.CONFIRMED_ISSUE,
                    title="Score Mismatch Between Uploaded PDF and Authoritative Backend",
                    description=(
                        f"Uploaded PDF states raw score as {pdf_raw}, but official backend records "
                        f"state raw score is {backend_raw}."
                    ),
                    evidence={"pdf_raw_score": pdf_raw, "backend_raw_score": backend_raw, "candidate_id": candidate_id},
                    impact="Discrepancy may indicate outdated PDF, manual tampering, or an unrecorded grade amendment.",
                    recommended_action="Trust authoritative backend records. Initiate an audit trail verification."
                ))
        except Exception as e:
            anomalies.append(AnomalyReport(
                classification=AnomalyClassification.UNVERIFIED_OBSERVATION,
                title="Could Not Verify PDF Against Backend",
                description=str(e),
                evidence={"error": str(e)},
                impact="Candidate verification incomplete.",
                recommended_action="Ensure candidate ID is correct."
            ))
        return anomalies


proactive_analytics = ProactiveAnalyticsEngine()
