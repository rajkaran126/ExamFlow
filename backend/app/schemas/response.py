"""Response Schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict

class QuestionResponseSchema(BaseModel):
    id: Optional[str] = None
    candidateId: str
    examinationId: str
    sectionId: str
    questionNumber: int
    selectedOption: Optional[str] = None
    status: str
    timestamp: Optional[str] = None
    timeTaken: int = 0
    isLate: bool = False

    model_config = ConfigDict(from_attributes=True)

class CandidateResponsesSchema(BaseModel):
    candidateId: str
    examinationId: str
    responses: list[QuestionResponseSchema]
    submittedAt: Optional[str] = None
