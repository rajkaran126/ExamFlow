"""Examination & Section Schemas."""
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class SectionSchema(BaseModel):
    id: Optional[str] = None
    name: str
    totalQuestions: int
    maxMarks: float
    marksPerQuestion: float
    negativeMarksPerQuestion: float
    cutoff: Optional[float] = None
    categoryWiseCutoffs: Optional[dict[str, float]] = None

    model_config = ConfigDict(from_attributes=True)

class ShiftSchema(BaseModel):
    id: Optional[str] = None
    examinationId: Optional[str] = None
    name: str
    date: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    totalCandidates: int = 0
    status: str = "SCHEDULED"

    model_config = ConfigDict(from_attributes=True)

class ExaminationSchema(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    description: Optional[str] = None
    date: Optional[str] = None
    duration: int
    totalMarks: float
    passingMarks: float
    sections: list[SectionSchema] = []
    shifts: list[ShiftSchema] = []
    negativeMarkingEnabled: bool = True
    sectionalCutoffsEnabled: bool = True
    normalisationEnabled: bool = True
    status: str = "DRAFT"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
