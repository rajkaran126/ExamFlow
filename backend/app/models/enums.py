"""Common Enumerations for ExamFlow."""
import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EXAMINER = "EXAMINER"
    MODERATOR = "MODERATOR"
    VIEWER = "VIEWER"
    CANDIDATE = "CANDIDATE"


class CandidateCategory(str, enum.Enum):
    GEN = "GEN"
    GENERAL = "GENERAL"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class CandidateStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    APPEARED = "APPEARED"
    ABSENT = "ABSENT"
    DISQUALIFIED = "DISQUALIFIED"


class ExamStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    RESULTS_DECLARED = "RESULTS_DECLARED"


class ShiftStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResponseStatus(str, enum.Enum):
    OPTION_SELECTED = "OPTION_SELECTED"
    ANSWERED = "ANSWERED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    MARKED_FOR_REVIEW = "MARKED_FOR_REVIEW"
    ANSWERED_AND_MARKED_FOR_REVIEW = "ANSWERED_AND_MARKED_FOR_REVIEW"


class ChallengeStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


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


class ReEvaluationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class ProctoringSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
