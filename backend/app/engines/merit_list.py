"""Merit List and Tie-Breaking Engine (Rule 9, Rule 10, Rule 12)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.engines.enums import CandidateCategory


@dataclass
class CandidateMeritRecord:
    candidate_id: str
    name: str
    roll_number: str
    category: str
    shift_name: str
    date_of_birth: str  # YYYY-MM-DD
    raw_score: Decimal
    normalised_score: Decimal
    relevant_sectional_score: Decimal # first section by ordering
    wrong_count: int
    qualified: bool


@dataclass
class RankedMeritEntry:
    rank: int
    category_rank: Optional[int]
    candidate_id: str
    name: str
    roll_number: str
    category: str
    shift_name: str
    total_marks: Decimal
    normalised_score: Decimal
    qualification_status: str
    is_selected: bool
    tie_unresolved: bool
    allocated_under_gen: bool


def compare_merit_records(c1: CandidateMeritRecord, c2: CandidateMeritRecord) -> int:
    """
    Rule 9 – Merit list ordering tie-breaker:
    1. Higher normalised score (descending)
    2. Higher relevant sectional score (descending)
    3. Fewer incorrect answers (ascending)
    4. Older date of birth (ascending - older person has earlier date)
    5. Alphabetical name (ascending)
    Returns: -1 if c1 > c2 (c1 ranks better), 1 if c2 > c1, 0 if full tie
    """
    # 1. Higher normalised score
    if c1.normalised_score != c2.normalised_score:
        return -1 if c1.normalised_score > c2.normalised_score else 1

    # 2. Higher relevant sectional score
    if c1.relevant_sectional_score != c2.relevant_sectional_score:
        return -1 if c1.relevant_sectional_score > c2.relevant_sectional_score else 1

    # 3. Fewer incorrect answers
    if c1.wrong_count != c2.wrong_count:
        return -1 if c1.wrong_count < c2.wrong_count else 1

    # 4. Older date of birth (earlier YYYY-MM-DD is older)
    if c1.date_of_birth != c2.date_of_birth:
        return -1 if c1.date_of_birth < c2.date_of_birth else 1

    # 5. Alphabetical name
    if c1.name.lower() != c2.name.lower():
        return -1 if c1.name.lower() < c2.name.lower() else 1

    # Exact full tie
    return 0


def generate_merit_list_entries(
    records: list[CandidateMeritRecord],
    vacancies: int = 100,
    category_vacancies: dict[str, int] = None
) -> list[RankedMeritEntry]:
    """
    Generates deterministic rankings applying all tie-breakers,
    handles unresolved ties gracefully, and allocates reserved category
    candidates scoring above the GEN threshold against the GEN quota (Rule 10).
    """
    from functools import cmp_to_key

    category_vacancies = category_vacancies or {}

    # Filter to qualified candidates only for selection
    # Sort deterministically
    sorted_records = sorted(records, key=cmp_to_key(compare_merit_records))

    entries: list[RankedMeritEntry] = []
    category_counters: dict[str, int] = {}
    
    # Track GEN cutoff (threshold of the last candidate selected under GEN quota)
    gen_quota = category_vacancies.get("GEN", vacancies)
    gen_threshold_score: Optional[Decimal] = None

    current_rank = 1
    i = 0
    while i < len(sorted_records):
        rec = sorted_records[i]
        
        # Check if tie exists with next candidate
        is_tied = False
        if i + 1 < len(sorted_records) and compare_merit_records(rec, sorted_records[i+1]) == 0:
            is_tied = True
        elif i > 0 and compare_merit_records(rec, sorted_records[i-1]) == 0:
            is_tied = True

        # Category rank
        cat_rank = category_counters.get(rec.category, 0) + 1
        category_counters[rec.category] = cat_rank

        # Selection logic (Rule 10)
        # SC/ST/OBC scoring above GEN threshold allocated to GEN quota
        allocated_gen = False
        selected = False

        if current_rank <= gen_quota:
            selected = True
            allocated_gen = True
            gen_threshold_score = rec.normalised_score
        else:
            cat_vac = category_vacancies.get(rec.category, 0)
            if cat_rank <= cat_vac:
                selected = True

        entries.append(RankedMeritEntry(
            rank=current_rank,
            category_rank=cat_rank,
            candidate_id=rec.candidate_id,
            name=rec.name,
            roll_number=rec.roll_number,
            category=rec.category,
            shift_name=rec.shift_name,
            total_marks=rec.raw_score,
            normalised_score=rec.normalised_score,
            qualification_status="QUALIFIED" if rec.qualified else "NOT_QUALIFIED",
            is_selected=selected,
            tie_unresolved=is_tied,
            allocated_under_gen=allocated_gen
        ))

        current_rank += 1
        i += 1

    return entries
