"""Pure Python enums for deterministic calculation engines."""
import enum

class ResponseStatus(str, enum.Enum):
    OPTION_SELECTED = "OPTION_SELECTED"
    ANSWERED = "ANSWERED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    MARKED_FOR_REVIEW = "MARKED_FOR_REVIEW"
    ANSWERED_AND_MARKED_FOR_REVIEW = "ANSWERED_AND_MARKED_FOR_REVIEW"

class DroppedQuestionScoringRule(str, enum.Enum):
    AWARD_ALL = "AWARD_ALL"
    AWARD_NONE = "AWARD_NONE"
    AWARD_CORRECT_ONLY = "AWARD_CORRECT_ONLY"

class QualificationStatus(str, enum.Enum):
    QUALIFIED = "QUALIFIED"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    FAILED = "FAILED"
    DISQUALIFIED = "DISQUALIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"

class CandidateCategory(str, enum.Enum):
    GEN = "GEN"
    GENERAL = "GENERAL"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"
