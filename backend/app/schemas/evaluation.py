"""Evaluation & Result Schemas."""
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class SectionResultSchema(BaseModel):
    sectionId: str
    sectionName: str
    totalQuestions: int
    attempted: int
    correct: int
    incorrect: int
    marksObtained: float
    cutoff: float
    isQualified: bool
    disqualificationReason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EvaluationResultSchema(BaseModel):
    id: Optional[str] = None
    candidateId: str
    candidateName: Optional[str] = None
    rollNumber: Optional[str] = None
    examinationId: str
    shiftId: Optional[str] = None
    sectionResults: list[SectionResultSchema] = []
    totalQuestions: int
    attemptedQuestions: int
    correctAnswers: int
    incorrectAnswers: int
    totalPositiveMarks: float
    totalNegativeMarks: float
    totalMarks: float
    proctoringPenalty: float = 0.0
    finalMarks: float
    normalisedScore: Optional[float] = None
    qualificationStatus: str
    failureReasons: list[str] = []
    evaluatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
