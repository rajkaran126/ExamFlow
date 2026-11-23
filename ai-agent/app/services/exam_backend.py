"""Authoritative PS-072 Examination Engine and Data Store.
Implements raw score calculation, negative marking, sectional cut-offs, minimum attempts,
proctoring deductions/disqualifications, shift normalisation, and merit list tie-breakers.
"""
import copy
import time
import math
from typing import Dict, List, Any, Optional, Tuple
from app.models import (
    CandidateScorecard, ShiftStatistics, CandidateCategory,
    QualificationStatus, PreparedAction, PreparationStatus, UserRole
)
from app.permissions import permission_manager

class ExamBackendService:
    """The authoritative examination computation engine for PS-072."""

    def __init__(self):
        self.exam_id = "EXAM-2026-GATE"
        self.result_version = "v1.0"
        self.evaluation_history: List[Dict[str, Any]] = []
        self.prepared_actions: Dict[str, PreparedAction] = {}
        
        # Rule register
        self.rules = {
            "total_questions": 65,
            "max_marks": 100.0,
            "negative_marking_ratio": 1/3, # -1/3 marks for 1-mark question, -2/3 for 2-mark
            "minimum_attempt_percent": 30.0, # At least 30% of questions attempted
            "sectional_cutoffs": {
                "Section_A": 3.5,   # General Aptitude (out of 15)
                "Section_B": 25.0   # Technical Engineering (out of 85)
            },
            "category_aggregate_cutoffs": {
                CandidateCategory.GEN: 28.5,
                CandidateCategory.EWS: 26.0,
                CandidateCategory.OBC_NCL: 25.6,
                CandidateCategory.SC: 19.0,
                CandidateCategory.ST: 19.0,
                CandidateCategory.PWD: 19.0
            },
            "proctoring_integrity_threshold": 40.0, # Below 40 is immediate disqualification
            "proctoring_deduction_threshold": 80.0, # Below 80 deducts marks
            "proctoring_penalty_rate": 0.25 # 0.25 marks deducted per point below 80
        }
        
        # Answer keys by shift
        self.answer_keys: Dict[str, Dict[str, Any]] = {
            "SHIFT-1": {
                f"Q{i}": {"correct": "B" if i % 2 == 0 else "A", "marks": 2 if i > 10 else 1, "type": "MCQ", "dropped": False}
                for i in range(1, 66)
            },
            "SHIFT-2": {
                f"Q{i}": {"correct": "C" if i % 3 == 0 else "D", "marks": 2 if i > 10 else 1, "type": "MCQ", "dropped": (i == 42)}
                for i in range(1, 66)
            },
            "SHIFT-3": {
                f"Q{i}": {"correct": "A" if i % 4 == 0 else "B", "marks": 2 if i > 10 else 1, "type": "MCQ", "dropped": False}
                for i in range(1, 66)
            }
        }

        # Initialize candidate database with realistic variation
        self._init_candidates()
        self._compute_shift_statistics()

    def _init_candidates(self):
        """Seed realistic candidates across 3 shifts."""
        self.candidates: Dict[str, Dict[str, Any]] = {}
        
        # Candidate profiles template
        profiles = [
            # Shift 1: High performing
            ("CAND-1001", "Aarav Sharma", "SHIFT-1", CandidateCategory.GEN, False, 58, 52, 6, 85.5, 96.0, "2000-05-14"),
            ("CAND-1002", "Priya Patel", "SHIFT-1", CandidateCategory.OBC_NCL, False, 52, 44, 8, 71.0, 92.0, "2001-08-22"),
            ("CAND-1003", "Rohan Verma", "SHIFT-1", CandidateCategory.SC, False, 45, 32, 13, 44.5, 88.0, "1999-11-03"),
            ("CAND-1004", "Ananya Iyer", "SHIFT-1", CandidateCategory.EWS, False, 60, 56, 4, 89.0, 99.0, "2001-01-19"),
            ("CAND-1005", "Devendra Das", "SHIFT-1", CandidateCategory.PWD, True, 38, 26, 12, 34.0, 94.0, "1998-07-12"),

            # Shift 2: Known anomaly shift (Tough Section B, harsh proctoring, dropped Q42)
            ("CAND-2001", "Vikram Malhotra", "SHIFT-2", CandidateCategory.GEN, False, 46, 30, 16, 38.0, 72.0, "2000-03-10"),
            ("CAND-2002", "Sneha Mukherjee", "SHIFT-2", CandidateCategory.GEN, False, 32, 18, 14, 19.5, 35.0, "2001-09-15"), # Proctoring disqualified (<40)
            ("CAND-2003", "Karan Johar", "SHIFT-2", CandidateCategory.OBC_NCL, False, 18, 12, 6, 14.0, 91.0, "2000-12-05"),  # Minimum attempts failed (<20)
            ("CAND-2004", "Meera Nambiar", "SHIFT-2", CandidateCategory.SC, False, 44, 25, 19, 26.0, 85.0, "2002-04-20"),
            ("CAND-2005", "Arjun Reddy", "SHIFT-2", CandidateCategory.GEN, False, 48, 28, 20, 31.0, 68.0, "1999-06-30"),    # Section B cut-off failure
            ("CAND-2006", "Pooja Hegde", "SHIFT-2", CandidateCategory.PWD, True, 36, 21, 15, 23.5, 95.0, "2001-02-18"),

            # Shift 3: Balanced shift
            ("CAND-3001", "Rahul Dravid", "SHIFT-3", CandidateCategory.GEN, False, 54, 46, 8, 73.0, 98.0, "2000-10-10"),
            ("CAND-3002", "Smriti Mandhana", "SHIFT-3", CandidateCategory.OBC_NCL, False, 50, 40, 10, 62.5, 94.0, "2001-07-18"),
            ("CAND-3003", "Harmanpreet Kaur", "SHIFT-3", CandidateCategory.SC, False, 42, 30, 12, 42.0, 89.0, "1999-03-08")
        ]

        # Seed candidate responses and scorecards
        for c_id, name, shift, cat, pwd, att, corr, wrg, raw, integ, dob in profiles:
            # Section distribution
            sec_a_att = min(att, 10)
            sec_b_att = att - sec_a_att
            sec_a_marks = round(max(0.0, (sec_a_att * 0.7) - (sec_a_att * 0.3 * 0.33)), 2)
            sec_b_marks = round(max(0.0, raw - sec_a_marks), 2)
            
            # Negative penalties
            neg_pen = round(wrg * (1/3), 2)
            
            # Proctoring deductions
            proctor_ded = 0.0
            if integ < self.rules["proctoring_deduction_threshold"]:
                proctor_ded = round((self.rules["proctoring_deduction_threshold"] - integ) * self.rules["proctoring_penalty_rate"], 2)
            
            # Disqualification checks
            proctor_disq = (integ < self.rules["proctoring_integrity_threshold"])
            min_att_cleared = (att >= 20)
            sec_cleared = (sec_a_marks >= self.rules["sectional_cutoffs"]["Section_A"]) and (sec_b_marks >= self.rules["sectional_cutoffs"]["Section_B"])
            
            # Initial normalized score placeholder (computed during normalisation)
            norm_score = raw # will be updated

            self.candidates[c_id] = {
                "id": c_id,
                "name": name,
                "shift_id": shift,
                "category": cat,
                "is_pwd": pwd,
                "dob": dob,
                "attempted": att,
                "correct": corr,
                "wrong": wrg,
                "raw_score": raw,
                "sec_a_marks": sec_a_marks,
                "sec_b_marks": sec_b_marks,
                "negative_penalties": neg_pen,
                "proctoring_integrity": integ,
                "proctoring_deductions": proctor_ded,
                "proctoring_disqualified": proctor_disq,
                "minimum_attempts_cleared": min_att_cleared,
                "sectional_cutoffs_cleared": sec_cleared,
                "normalized_score": norm_score,
                "responses": {f"Q{q}": "CORRECT" if q <= corr else ("WRONG" if q <= att else "UNATTEMPTED") for q in range(1, 66)}
            }

        # Apply Equipercentile / Shift Normalisation
        self._apply_shift_normalisation()

    def _apply_shift_normalisation(self):
        """Applies Mean-Std Dev shift normalisation across shifts with mathematical guards."""
        shifts = ["SHIFT-1", "SHIFT-2", "SHIFT-3"]
        shift_data: Dict[str, List[float]] = {s: [] for s in shifts}
        all_scores: List[float] = []

        for c in self.candidates.values():
            if not c["proctoring_disqualified"]:
                shift_data[c["shift_id"]].append(c["raw_score"])
                all_scores.append(c["raw_score"])

        # Global statistics
        mean_global = sum(all_scores) / len(all_scores) if all_scores else 50.0
        std_global = math.sqrt(sum((x - mean_global) ** 2 for x in all_scores) / len(all_scores)) if len(all_scores) > 1 else 10.0
        
        # Shift statistics
        shift_stats = {}
        for s in shifts:
            scores = shift_data[s]
            if len(scores) >= 2:
                m = sum(scores) / len(scores)
                sd = math.sqrt(sum((x - m) ** 2 for x in scores) / len(scores))
            else:
                m, sd = 50.0, 10.0
            shift_stats[s] = {"mean": m, "std": max(sd, 1.0)}

        # Normalization calculation per candidate
        for c in self.candidates.values():
            if c["proctoring_disqualified"]:
                c["normalized_score"] = 0.0
                c["qualification_status"] = QualificationStatus.DISQUALIFIED
                c["disqualification_reason"] = f"Proctoring Malpractice: Integrity score {c['proctoring_integrity']:.1f}% below 40% threshold."
                continue

            s = c["shift_id"]
            m_i = shift_stats[s]["mean"]
            sd_i = shift_stats[s]["std"]

            # Standard formula: (raw - m_i)/sd_i * std_global + mean_global - proctoring_deductions
            standardized = (c["raw_score"] - m_i) / sd_i
            normalized = (standardized * std_global) + mean_global - c["proctoring_deductions"]

            # Normalization guards (clamped between 0 and 100)
            c["normalized_score"] = round(min(100.0, max(0.0, normalized)), 2)

            # Qualification determination
            agg_cutoff = self.rules["category_aggregate_cutoffs"][c["category"]]
            if c["is_pwd"]:
                agg_cutoff = self.rules["category_aggregate_cutoffs"][CandidateCategory.PWD]

            if not c["minimum_attempts_cleared"]:
                c["qualification_status"] = QualificationStatus.NOT_QUALIFIED
                c["disqualification_reason"] = f"Failed Minimum Attempts: Attempted {c['attempted']} questions (minimum required is 20)."
            elif not c["sectional_cutoffs_cleared"]:
                c["qualification_status"] = QualificationStatus.NOT_QUALIFIED
                c["disqualification_reason"] = f"Failed Sectional Cut-offs: Sec A={c['sec_a_marks']} (min 3.5), Sec B={c['sec_b_marks']} (min 25.0)."
            elif c["normalized_score"] < agg_cutoff:
                c["qualification_status"] = QualificationStatus.NOT_QUALIFIED
                c["disqualification_reason"] = f"Below Category Aggregate Cut-off: Normalized score {c['normalized_score']} < Cut-off {agg_cutoff} ({c['category'].value})."
            else:
                c["qualification_status"] = QualificationStatus.QUALIFIED
                c["disqualification_reason"] = None

        # Compute Merit List Ranks with multi-tier tie-breakers
        # Tie breaker 1: Normalized score (descending)
        # Tie breaker 2: Section B Technical Marks (descending)
        # Tie breaker 3: Fewer negative penalties (ascending)
        # Tie breaker 4: Older age (ascending DOB)
        qualified = [c for c in self.candidates.values() if c["qualification_status"] == QualificationStatus.QUALIFIED]
        qualified.sort(key=lambda x: (
            -x["normalized_score"],
            -x["sec_b_marks"],
            x["negative_penalties"],
            x["dob"]
        ))
        
        for rank, c in enumerate(qualified, 1):
            c["rank"] = rank

    def _compute_shift_statistics(self):
        """Aggregate shift performance metrics for anomaly detection and analysis."""
        self.shift_stats: Dict[str, ShiftStatistics] = {}
        for s in ["SHIFT-1", "SHIFT-2", "SHIFT-3"]:
            cands = [c for c in self.candidates.values() if c["shift_id"] == s]
            appeared = len(cands)
            scores = [c["raw_score"] for c in cands]
            qualified_count = sum(1 for c in cands if c["qualification_status"] == QualificationStatus.QUALIFIED)
            
            mean_sc = sum(scores) / appeared if appeared > 0 else 0.0
            std_sc = math.sqrt(sum((x - mean_sc)**2 for x in scores) / appeared) if appeared > 1 else 0.0
            
            sec_failures = {
                "Section_A": sum(1 for c in cands if c["sec_a_marks"] < self.rules["sectional_cutoffs"]["Section_A"]),
                "Section_B": sum(1 for c in cands if c["sec_b_marks"] < self.rules["sectional_cutoffs"]["Section_B"])
            }
            min_att_fails = sum(1 for c in cands if not c["minimum_attempts_cleared"])
            proctor_disqs = sum(1 for c in cands if c["proctoring_disqualified"])

            self.shift_stats[s] = ShiftStatistics(
                exam_id=self.exam_id,
                shift_id=s,
                total_registered=appeared + 5,
                total_appeared=appeared,
                mean_raw_score=round(mean_sc, 2),
                std_dev_raw_score=round(std_sc, 2),
                min_score=min(scores) if scores else 0.0,
                max_score=max(scores) if scores else 0.0,
                total_qualified=qualified_count,
                qualification_rate_percent=round((qualified_count / appeared * 100) if appeared > 0 else 0.0, 2),
                sectional_failure_counts=sec_failures,
                minimum_attempt_failure_count=min_att_fails,
                proctoring_disqualification_count=proctor_disqs,
                is_pooled=(appeared < 30)
            )

    # --- Tool Execution Methods ---

    def get_exam_details(self, exam_id: str) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "title": "GATE 2026 - Computer Science & Information Technology",
            "shifts": ["SHIFT-1", "SHIFT-2", "SHIFT-3"],
            "total_questions": self.rules["total_questions"],
            "max_marks": self.rules["max_marks"],
            "result_version": self.result_version,
            "normalisation_method": "Mean-Standard Deviation Multi-Shift Normalisation with Clamping Guards",
            "sectional_cutoffs": self.rules["sectional_cutoffs"],
            "category_cutoffs": {k.value: v for k, v in self.rules["category_aggregate_cutoffs"].items()}
        }

    def get_candidate_details(self, candidate_id: str, exam_id: Optional[str] = None) -> Dict[str, Any]:
        c = self.candidates.get(candidate_id)
        if not c:
            raise ValueError(f"Candidate '{candidate_id}' not found.")
        return {
            "candidate_id": c["id"],
            "candidate_name": c["name"],
            "shift_id": c["shift_id"],
            "category": c["category"].value,
            "is_pwd": c["is_pwd"],
            "dob": c["dob"],
            "exam_id": self.exam_id
        }

    def get_candidate_scorecard(self, candidate_id: str, exam_id: Optional[str] = None) -> Dict[str, Any]:
        c = self.candidates.get(candidate_id)
        if not c:
            raise ValueError(f"Candidate '{candidate_id}' not found in examination records.")
        return {
            "candidate_id": c["id"],
            "candidate_name": c["name"],
            "exam_id": self.exam_id,
            "shift_id": c["shift_id"],
            "category": c["category"].value,
            "is_pwd": c["is_pwd"],
            "attempted_questions": c["attempted"],
            "total_questions": self.rules["total_questions"],
            "attempt_percentage": round((c["attempted"] / self.rules["total_questions"]) * 100, 2),
            "raw_score": c["raw_score"],
            "sectional_scores": {
                "Section_A": c["sec_a_marks"],
                "Section_B": c["sec_b_marks"]
            },
            "negative_penalties": c["negative_penalties"],
            "proctoring_deductions": c["proctoring_deductions"],
            "normalized_score": c["normalized_score"],
            "proctoring_integrity_score": c["proctoring_integrity"],
            "proctoring_disqualified": c["proctoring_disqualified"],
            "sectional_cutoffs_cleared": c["sectional_cutoffs_cleared"],
            "minimum_attempts_cleared": c["minimum_attempts_cleared"],
            "qualification_status": c["qualification_status"].value,
            "disqualification_reason": c["disqualification_reason"],
            "rank": c.get("rank"),
            "result_version": self.result_version
        }

    def get_candidate_responses(self, candidate_id: str, exam_id: Optional[str] = None) -> Dict[str, Any]:
        c = self.candidates.get(candidate_id)
        if not c:
            raise ValueError(f"Candidate '{candidate_id}' not found.")
        return {
            "candidate_id": c["id"],
            "shift_id": c["shift_id"],
            "attempted": c["attempted"],
            "correct": c["correct"],
            "wrong": c["wrong"],
            "responses_sample": {k: c["responses"][k] for k in list(c["responses"].keys())[:15]},
            "total_responses": len(c["responses"])
        }

    def get_answer_key(self, exam_id: str, shift_id: str) -> Dict[str, Any]:
        if shift_id not in self.answer_keys:
            raise ValueError(f"Invalid shift '{shift_id}'. Available: SHIFT-1, SHIFT-2, SHIFT-3.")
        keys = self.answer_keys[shift_id]
        dropped = [q for q, data in keys.items() if data.get("dropped")]
        return {
            "exam_id": exam_id,
            "shift_id": shift_id,
            "total_questions": len(keys),
            "dropped_questions": dropped,
            "sample_keys": {k: keys[k] for k in list(keys.keys())[:10]}
        }

    def get_shift_statistics(self, exam_id: str, shift_id: str) -> Dict[str, Any]:
        if shift_id not in self.shift_stats:
            raise ValueError(f"Shift '{shift_id}' not recognized.")
        return self.shift_stats[shift_id].model_dump()

    def get_proctoring_report(self, candidate_id: str, exam_id: Optional[str] = None) -> Dict[str, Any]:
        c = self.candidates.get(candidate_id)
        if not c:
            raise ValueError(f"Candidate '{candidate_id}' not found.")
        return {
            "candidate_id": c["id"],
            "integrity_score": c["proctoring_integrity"],
            "disqualified": c["proctoring_disqualified"],
            "penalties_applied": c["proctoring_deductions"],
            "events_logged": [
                {"timestamp": "10:14:22", "event": "Tab focus lost", "penalty": 5},
                {"timestamp": "10:45:10", "event": "Multiple faces detected", "penalty": 15}
            ] if c["proctoring_integrity"] < 80 else []
        }

    def get_qualification_status(self, candidate_id: str, exam_id: Optional[str] = None) -> Dict[str, Any]:
        c = self.candidates.get(candidate_id)
        if not c:
            raise ValueError(f"Candidate '{candidate_id}' not found.")
        return {
            "candidate_id": c["id"],
            "status": c["qualification_status"].value,
            "reason": c["disqualification_reason"] or "Candidate has met all sectional, attempt, and aggregate criteria.",
            "normalized_score": c["normalized_score"],
            "category": c["category"].value,
            "rank": c.get("rank")
        }

    def get_merit_list(self, exam_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        qualified = [c for c in self.candidates.values() if c["qualification_status"] == QualificationStatus.QUALIFIED]
        if category:
            qualified = [c for c in qualified if c["category"].value == category]
        qualified.sort(key=lambda x: x.get("rank", 999))
        return {
            "exam_id": self.exam_id,
            "result_version": self.result_version,
            "total_qualified": len(qualified),
            "merit_list": [
                {
                    "rank": c.get("rank"),
                    "candidate_id": c["id"],
                    "candidate_name": c["name"],
                    "category": c["category"].value,
                    "normalized_score": c["normalized_score"],
                    "shift_id": c["shift_id"]
                }
                for c in qualified
            ]
        }

    def get_category_cutoffs(self, exam_id: str) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "sectional_cutoffs": self.rules["sectional_cutoffs"],
            "category_aggregate_cutoffs": {k.value: v for k, v in self.rules["category_aggregate_cutoffs"].items()},
            "minimum_attempt_percent": self.rules["minimum_attempt_percent"]
        }

    def get_evaluation_history(self, candidate_id: Optional[str] = None, exam_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "current_version": self.result_version,
            "history_log": self.evaluation_history
        }

    # --- Prepared-Action Tools (Level 4) ---

    def prepare_result_report(self, exam_id: str, shift_id: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> PreparedAction:
        target = f"{exam_id}:{shift_id or 'ALL'}"
        token = permission_manager.generate_approval_token(target, "prepare_result_report")
        prep = PreparedAction(
            tool_name="prepare_result_report",
            arguments={"exam_id": exam_id, "shift_id": shift_id, "options": options or {}},
            summary=f"Compile official finalized result report for {target}.",
            target_identifier=target,
            consequences=["Generates cryptographically signed official score ledger for all candidates in shift."],
            approver_token=token,
            expires_at=time.time() + 900,
            required_role=UserRole.EXAM_ADMIN
        )
        self.prepared_actions[prep.preparation_id] = prep
        return prep

    def prepare_reevaluation_request(self, candidate_id: str, exam_id: str, justification: str, affected_questions: List[str]) -> PreparedAction:
        token = permission_manager.generate_approval_token(candidate_id, "prepare_reevaluation_request")
        prep = PreparedAction(
            tool_name="prepare_reevaluation_request",
            arguments={
                "candidate_id": candidate_id,
                "exam_id": exam_id,
                "justification": justification,
                "affected_questions": affected_questions
            },
            summary=f"Request formal re-evaluation for Candidate {candidate_id} on questions {affected_questions}.",
            target_identifier=candidate_id,
            consequences=[
                f"Candidate raw and normalized scores will be recalculated.",
                f"New result version will be created for Candidate {candidate_id}."
            ],
            approver_token=token,
            expires_at=time.time() + 900,
            required_role=UserRole.EXAM_ADMIN
        )
        self.prepared_actions[prep.preparation_id] = prep
        return prep

    def prepare_answer_key_update(self, exam_id: str, shift_id: str, question_id: str, proposed_action: str, new_correct_options: List[str], reason: str) -> PreparedAction:
        target = f"{shift_id}:{question_id}"
        token = permission_manager.generate_approval_token(target, "prepare_answer_key_update")
        prep = PreparedAction(
            tool_name="prepare_answer_key_update",
            arguments={
                "exam_id": exam_id,
                "shift_id": shift_id,
                "question_id": question_id,
                "proposed_action": proposed_action,
                "new_correct_options": new_correct_options,
                "reason": reason
            },
            summary=f"Update answer key for {question_id} in {shift_id} to {proposed_action}.",
            target_identifier=target,
            consequences=[
                f"Will alter answer key for all candidates in {shift_id}.",
                "Triggers global score re-normalization across all shifts.",
                "Increments exam result version to v1.1."
            ],
            approver_token=token,
            expires_at=time.time() + 900,
            required_role=UserRole.EXAM_ADMIN
        )
        self.prepared_actions[prep.preparation_id] = prep
        return prep

    def prepare_merit_list_publication(self, exam_id: str, version_tag: str, scheduled_time: Optional[str] = None) -> PreparedAction:
        token = permission_manager.generate_approval_token(exam_id, "prepare_merit_list_publication")
        prep = PreparedAction(
            tool_name="prepare_merit_list_publication",
            arguments={"exam_id": exam_id, "version_tag": version_tag, "scheduled_time": scheduled_time},
            summary=f"Publish final merit list for {exam_id} (Version {version_tag}).",
            target_identifier=exam_id,
            consequences=[
                "Makes candidate ranks permanently public to candidates and institutions.",
                "Locks result modifications for this version."
            ],
            approver_token=token,
            expires_at=time.time() + 900,
            required_role=UserRole.EXAM_ADMIN
        )
        self.prepared_actions[prep.preparation_id] = prep
        return prep

    # --- Consequential Tools (Level 5) ---

    
    
    def execute_reevaluation(
        self,
        preparation_id: str,
        approver_token: str,
        user_role: UserRole,
        approver_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate an approved re-evaluation request.

        Actual execution remains disabled until the authoritative
        scoring service is integrated.
        """

        prep = self.prepared_actions.get(preparation_id)

        if not prep:
            raise ValueError(
                f"Prepared action '{preparation_id}' not found."
            )

        # Validate lifecycle first, including replay prevention.
        # The permission manager checks the action status before
        # requiring approver_id.
        valid, err = permission_manager.validate_approval(
            prep,
            approver_token,
            user_role,
            approver_id=approver_id
        )

        if not valid:
            raise PermissionError(err)

        # Never fabricate marks or modify candidate scores.
        raise NotImplementedError(
            "Re-evaluation execution is disabled until the "
            "authoritative exam scoring service is integrated."
        )


    
    
    def approve_answer_key_change(
        self,
        preparation_id: str,
        approver_token: str,
        user_role: UserRole,
        approver_id: str
    ) -> Dict[str, Any]:
        """Validate and transactionally commit an authorized answer-key change."""

        prep = self.prepared_actions.get(preparation_id)

        if not prep:
            raise ValueError(
                f"Prepared action '{preparation_id}' not found."
            )

        # Validate all proposed changes before authorizing execution.
        shift_id = prep.arguments.get("shift_id")
        question_id = prep.arguments.get("question_id")
        proposed_action = prep.arguments.get("proposed_action")

        if not isinstance(shift_id, str) or shift_id not in self.answer_keys:
            raise ValueError(f"Shift '{shift_id}' not found.")

        if not isinstance(question_id, str) or question_id not in self.answer_keys[shift_id]:
            raise ValueError(f"Question '{question_id}' not found.")

        if proposed_action not in ("DROP", "CHANGE_OPTION"):
            raise ValueError(
                f"Unsupported answer-key action: {proposed_action}"
            )

        options = prep.arguments.get("new_correct_options", [])

        if proposed_action == "CHANGE_OPTION":
            if (
                not isinstance(options, list)
                or not options
                or not all(
                    isinstance(option, str) and option.strip()
                    for option in options
                )
            ):
                raise ValueError(
                    "Valid replacement correct options are required."
                )

        # Verify approval only after input validation.
        valid, err = permission_manager.validate_approval(
            prep,
            approver_token,
            user_role,
            approver_id=approver_id
        )

        if not valid:
            raise PermissionError(err)

        # Snapshot every state component affected by the operation.
        original_answer = copy.deepcopy(
            self.answer_keys[shift_id][question_id]
        )
        original_candidates = copy.deepcopy(self.candidates)
        original_shift_stats = copy.deepcopy(self.shift_stats)
        original_result_version = self.result_version

        try:
            if proposed_action == "DROP":
                self.answer_keys[shift_id][question_id]["dropped"] = True

            elif proposed_action == "CHANGE_OPTION":
                self.answer_keys[shift_id][question_id]["correct"] = options[0]

            self._apply_shift_normalisation()
            self._compute_shift_statistics()

            self.result_version = "v1.1"

        except Exception:
            # Restore all state if any part of the operation fails.
            self.answer_keys[shift_id][question_id] = original_answer
            self.candidates = original_candidates
            self.shift_stats = original_shift_stats
            self.result_version = original_result_version
            raise

        # Record approval only after the operation succeeds.
        prep.approved_by = approver_id.strip()
        prep.approval_role = user_role
        prep.approved_at = time.time()
        prep.status = PreparationStatus.EXECUTED

        audit_entry = {
            "action": "ANSWER_KEY_UPDATED",
            "preparation_id": preparation_id,
            "shift_id": shift_id,
            "question_id": question_id,
            "action_taken": proposed_action,
            "approved_by": prep.approved_by,
            "approval_role": (
                prep.approval_role.value
                if prep.approval_role else None
            ),
            "approved_at": prep.approved_at,
            "timestamp": time.time(),
            "result_version": self.result_version
        }

        self.evaluation_history.append(audit_entry)

        return {
            "success": True,
            "message": (
                f"Answer key update approved and committed for "
                f"{question_id} in {shift_id}."
            ),
            "result_version": self.result_version,
            "approved_by": prep.approved_by
        }


    
    
    def publish_merit_list(
        self,
        preparation_id: str,
        approver_token: str,
        user_role: UserRole,
        approver_id: str
    ) -> Dict[str, Any]:
        """Publish the merit list after authorized approval."""

        prep = self.prepared_actions.get(preparation_id)

        if not prep:
            raise ValueError(
                f"Prepared action '{preparation_id}' not found."
            )

        valid, err = permission_manager.validate_approval(
            prep,
            approver_token,
            user_role,
            approver_id=approver_id
        )

        if not valid:
            raise PermissionError(err)

        version = prep.arguments.get(
            "version_tag",
            self.result_version
        )

        total_qualified = sum(
            1 for candidate in self.candidates.values()
            if candidate["qualification_status"]
            == QualificationStatus.QUALIFIED
        )

        # Record approval only after validation succeeds.
        prep.approved_by = approver_id.strip()
        prep.approval_role = user_role
        prep.approved_at = time.time()
        prep.status = PreparationStatus.EXECUTED

        audit_entry = {
            "action": "MERIT_LIST_PUBLISHED",
            "preparation_id": preparation_id,
            "version": version,
            "approved_by": prep.approved_by,
            "approval_role": (
                prep.approval_role.value
                if prep.approval_role else None
            ),
            "approved_at": prep.approved_at,
            "timestamp": time.time()
        }

        self.evaluation_history.append(audit_entry)

        return {
            "success": True,
            "message": (
                f"Merit list publication recorded under version {version}."
            ),
            "total_qualified_candidates": total_qualified,
            "approved_by": prep.approved_by,
            "version": version
        }



exam_backend = ExamBackendService()
