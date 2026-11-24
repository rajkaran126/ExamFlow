# EXAMFLOW DECISION LOG (PS-072)

| Decision ID | Rule Reference | Description / Ambiguity | Resolution & Implementation | Approved Status |
|:---|:---|:---|:---|:---|
| **DL-001** | Rule 5 (Proctoring Penalty) | Base for proctoring percentage deduction: raw score vs net positive marks. | Calculated as percentage deduction applied against candidate's raw score. Clamped to 0 minimum if overall disqualified. | Approved |
| **DL-002** | Rule 6 (Normalisation Formula) | Small shift pooling order when multiple shifts have < 100 candidates. | All shifts with < 100 candidates are combined into a collective pooled distribution. | Approved |
| **DL-003** | Rule 7 (Normalisation Guard) | Behavior when denominator <= 0 (zero variance). | Engine raises `NormalisationGuardError` and halts calculation rather than substituting dummy variance or dividing by zero. | Approved |
| **DL-004** | Rule 8 (Minimum Attempts) | Boundary handling for exactly 10.00% attempt rate. | Explicitly treated as PASS (inclusive boundary: attempt_pct >= 10.00%). | Approved |
| **DL-005** | Rule 9 (Merit Tie-Breaker) | Section ordering for relevant sectional tie-breaker. | Ordering follows the `ordering` attribute of `ExaminationSection` (Section 1 primary). | Approved |
| **DL-006** | Rule 1 (Multi-correct Options) | Partial credit for partially correct multi-option answers. | Partial credit is NOT awarded. Candidate must match exact set of approved keys. Partial selection is penalized as wrong answer. | Approved |
| **DL-007** | Rule 11 (Re-Evaluation) | Multiple re-evaluation requests from same candidate. | Second request raises `ReEvaluationError` (Rule 11 one-time limit). | Approved |
