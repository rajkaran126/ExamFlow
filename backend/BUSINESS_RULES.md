# EXAMFLOW OFFICIAL BUSINESS RULE REGISTER
**Project:** AI-056  
**Problem Statement:** PS-072 – Online Exam Proctoring Result Engine with Negative Marking, Sectional Cut-offs and Shift Normalisation.  
**Role:** Senior Backend Architect & Examination-System Engineer (Team Member 2)

---

## Strict Rule Register & Implementation Mapping

### Rule 1 – Scoring
- **Description:** Correct responses receive configured `marks_per_correct`. Incorrect responses receive configured `negative_marks_per_wrong`. Not-attempted questions receive zero penalty. Multi-correct options require exact set match.
- **Implementation:** `app/engines/scoring.py::evaluate_question`, `score_candidate_responses`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_11_multiple_correct_options`

### Rule 2 – Dropped Questions & Key Changes
- **Description:** Dropped questions are scored according to configured rule: `AWARD_ALL` (full marks to all), `AWARD_NONE` (0 marks), or `AWARD_CORRECT_ONLY`. Updated answer keys recalculate candidate score versioning.
- **Implementation:** `app/engines/scoring.py::evaluate_question`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_10_dropped_question_marked_review_no_option`, `test_case_12_updated_answer_key`

### Rule 3 – Category Relaxation
- **Description:** Category relaxation applied to cut-off percentage:
  - OBC / EWS: 5 percentage points
  - SC / ST: 10 percentage points
  - PwD: additional 5 percentage points (cumulative)
- **Implementation:** `app/engines/qualification.py::get_category_relaxation_percentage`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_01_exact_sectional_cut_off`, `test_case_02_one_mark_below_cut_off`, `test_case_03_one_mark_above_cut_off`

### Rule 4 – Late Responses & Skipped Sections
- **Description:** Responses marked late are converted to `NOT_ATTEMPTED` with zero marks and zero penalty. Skipped sections fail sectional qualification.
- **Implementation:** `app/engines/scoring.py::evaluate_question`, `app/engines/qualification.py::evaluate_candidate_qualification`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_02_one_mark_below_cut_off`

### Rule 5 – Proctoring Penalties
- **Description:**
  - Severity 4–6: 5% score deduction
  - Severity 7–9: 15% score deduction
  - Severity 10 or above: Immediate Disqualification
  - Confirmed Malpractice: Immediate Disqualification
- **Implementation:** `app/engines/proctoring_penalty.py::calculate_proctoring_penalty`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_06_severity_6_penalty`, `test_case_07_severity_7_penalty`, `test_case_08_severity_9_penalty`, `test_case_09_severity_10_penalty`

### Rule 6 – Normalisation Formula & Pooling
- **Description:**
  $$S_{nij} = \left(rac{S_{ij} - M_j}{SD_j}ight) 	imes SD_g + M_g$$
  Shifts with fewer than 100 candidates (< 100) are pooled with adjacent shifts.
- **Implementation:** `app/engines/normalisation.py::normalise_examination_scores`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_13_shift_exactly_100_candidates`, `test_case_14_shift_with_99_candidates`

### Rule 7 – Normalisation Denominator Guard
- **Description:** If shift standard deviation $SD_j \le 0$, normalisation strictly raises `NormalisationGuardError`. Never silently divide by zero.
- **Implementation:** `app/engines/normalisation.py::normalise_examination_scores`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_15_normalisation_denominator_zero`, `test_case_16_normalisation_denominator_negative`

### Rule 8 – Minimum Attempts Threshold
- **Description:** Candidates attempting fewer than 10% of total examination questions fail. Exactly 10.00% is inclusive pass.
- **Implementation:** `app/engines/qualification.py::evaluate_candidate_qualification`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_04_exactly_10_percent_attempts`, `test_case_05_below_10_percent_attempts`

### Rule 9 – Merit List Tie-Breaking
- **Description:** Order of tie-breaking:
  1. Higher normalised score (descending)
  2. Higher relevant sectional score (descending)
  3. Fewer incorrect answers (ascending)
  4. Older date of birth (ascending)
  5. Alphabetical name (ascending)
  If all 5 match, `tie_unresolved=True` is recorded without arbitrary hidden rules.
- **Implementation:** `app/engines/merit_list.py::compare_merit_records`, `generate_merit_list_entries`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_17_full_merit_list_tie`

### Rule 10 – Category Cut-offs & GEN Allocation
- **Description:** Reserved-category candidates (SC/ST/OBC) scoring at or above the unreserved/GEN cut-off threshold are allocated against the GEN quota.
- **Implementation:** `app/engines/merit_list.py::generate_merit_list_entries`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_18_sc_candidate_above_gen_threshold`

### Rule 11 – Re-Evaluation Restriction
- **Description:** Exactly ONE re-evaluation allowed per candidate. Increments result version, preserves old result and audit history. Transactional.
- **Implementation:** `app/engines/re_evaluation.py::check_and_execute_re_evaluation`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_19_second_re_evaluation_attempt`

### Rule 12 – Precision & Rounding
- **Description:** Raw scores displayed to 2 decimal places. Normalised scores displayed to 5 decimal places. All arithmetic performed in Python `Decimal` with 28 digits of precision without premature rounding.
- **Implementation:** `app/engines/scoring.py`, `app/engines/normalisation.py`
- **Boundary Verification:** `tests/test_boundary_cases.py::test_case_20_score_precision_and_rounding`
