"""Engine Exceptions."""

class ExamEngineError(Exception):
    """Base exception for examination engine."""
    pass

class ScoringError(ExamEngineError):
    """Raised when an error occurs during scoring."""
    pass

class NormalisationError(ExamEngineError):
    """Raised when normalisation calculations fail or encounter invalid states."""
    pass

class NormalisationGuardError(NormalisationError):
    """Raised when normalisation denominator is zero or negative (Rule 7)."""
    pass

class QualificationError(ExamEngineError):
    """Raised when qualification logic encounters invalid inputs."""
    pass

class ReEvaluationError(ExamEngineError):
    """Raised when a candidate is not eligible for re-evaluation (Rule 11)."""
    pass
