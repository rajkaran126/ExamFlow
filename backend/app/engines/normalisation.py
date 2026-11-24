"""Shift Normalisation Engine (Rule 6, Rule 7, Rule 12)."""
import math
from dataclasses import dataclass
from decimal import Decimal, getcontext
from app.engines.exceptions import NormalisationGuardError

# Rule 12: Maintain high precision for normalisation calculations
getcontext().prec = 28


@dataclass
class ShiftStats:
    shift_id: str
    shift_name: str
    candidate_count: int
    mean_score: Decimal
    std_dev: Decimal
    max_score: Decimal
    min_score: Decimal
    is_pooled: bool = False


@dataclass
class NormalisationOutput:
    candidate_id: str
    shift_id: str
    raw_or_penalized_score: Decimal
    normalised_score: Decimal


def calculate_mean_and_std(scores: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Computes arithmetic mean and population standard deviation."""
    n = len(scores)
    if n == 0:
        return Decimal('0.00'), Decimal('0.00')

    mean = sum(scores) / Decimal(n)
    variance = sum((s - mean) ** 2 for s in scores) / Decimal(n)
    
    # Population standard deviation using math.sqrt converted back to Decimal
    std_dev = Decimal(str(math.sqrt(float(variance))))
    return mean, std_dev


def normalise_examination_scores(
    shifts_candidate_scores: dict[str, list[tuple[str, Decimal]]], # shift_id -> [(candidate_id, score)]
    shift_names: dict[str, str] = None
) -> tuple[dict[str, ShiftStats], list[NormalisationOutput]]:
    """
    Implements Rule 6 (Formula & Small-shift pooling) and Rule 7 (Denominator guard).

    Formula:
        Normalised Score S_nij for candidate i in shift j:
        S_nij = ((S_ij - M_j) / SD_j) * SD_g + M_g

    Where:
        S_ij: candidate score after penalty
        M_j: mean score of shift j
        SD_j: standard deviation of shift j
        M_g: global mean score across all shifts
        SD_g: global standard deviation across all shifts

    Small-shift pooling:
        Shifts with fewer than 100 candidates (< 100) are pooled together.
    """
    shift_names = shift_names or {}
    
    # Step 1: Small-shift pooling (Rule 6)
    # Check shifts with < 100 candidates
    isolated_shifts: dict[str, list[tuple[str, Decimal]]] = {}
    pooled_candidates: list[tuple[str, Decimal]] = []
    pooled_shift_ids = []

    for s_id, cand_list in shifts_candidate_scores.items():
        if len(cand_list) < 100 and len(shifts_candidate_scores) > 1:
            pooled_candidates.extend(cand_list)
            pooled_shift_ids.append(s_id)
        else:
            isolated_shifts[s_id] = cand_list

    # Step 2: Calculate Global Mean and Global Std Dev (M_g, SD_g)
    all_scores = [score for s_id in shifts_candidate_scores for _, score in shifts_candidate_scores[s_id]]
    if not all_scores:
        return {}, []

    global_mean, global_std = calculate_mean_and_std(all_scores)

    # Step 3: Compute Shift-wise Statistics
    shift_stats: dict[str, ShiftStats] = {}

    for s_id, cand_list in isolated_shifts.items():
        s_scores = [s for _, s in cand_list]
        m, sd = calculate_mean_and_std(s_scores)
        shift_stats[s_id] = ShiftStats(
            shift_id=s_id,
            shift_name=shift_names.get(s_id, s_id),
            candidate_count=len(s_scores),
            mean_score=m,
            std_dev=sd,
            max_score=max(s_scores) if s_scores else Decimal('0.00'),
            min_score=min(s_scores) if s_scores else Decimal('0.00'),
            is_pooled=False
        )

    if pooled_shift_ids:
        pooled_scores = [s for _, s in pooled_candidates]
        p_mean, p_sd = calculate_mean_and_std(pooled_scores)
        for s_id in pooled_shift_ids:
            s_cand = shifts_candidate_scores[s_id]
            s_scores = [s for _, s in s_cand]
            shift_stats[s_id] = ShiftStats(
                shift_id=s_id,
                shift_name=shift_names.get(s_id, s_id) + " (Pooled)",
                candidate_count=len(s_scores),
                mean_score=p_mean,
                std_dev=p_sd,
                max_score=max(s_scores) if s_scores else Decimal('0.00'),
                min_score=min(s_scores) if s_scores else Decimal('0.00'),
                is_pooled=True
            )

    # Step 4: Apply Normalisation Formula with Denominator Guard (Rule 7)
    normalised_results: list[NormalisationOutput] = []

    for s_id, cand_list in shifts_candidate_scores.items():
        stat = shift_stats[s_id]
        
        # Rule 7: Normalisation guard (denominator <= 0)
        if stat.std_dev <= Decimal('0.00'):
            raise NormalisationGuardError(
                f"Rule 7 Violation: Standard deviation (denominator) for shift '{s_id}' is <= 0 ({stat.std_dev}). Normalisation cannot proceed without variance."
            )

        for c_id, raw_sc in cand_list:
            # S_nij = ((S_ij - M_j) / SD_j) * SD_g + M_g
            z_score = (raw_sc - stat.mean_score) / stat.std_dev
            norm_score = (z_score * global_std) + global_mean
            
            # Preserve full precision (display to 5 decimal places later)
            normalised_results.append(NormalisationOutput(
                candidate_id=c_id,
                shift_id=s_id,
                raw_or_penalized_score=raw_sc,
                normalised_score=norm_score
            ))

    return shift_stats, normalised_results
