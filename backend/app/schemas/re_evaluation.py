"""Re-Evaluation Schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReEvaluationRequestSchema(BaseModel):
    id: Optional[str] = None
    candidateId: str
    examinationId: str
    reason: str
    status: str = "PENDING"
    originalMarks: float
    revisedMarks: Optional[float] = None
    requestedAt: Optional[str] = None
    resolvedAt: Optional[str] = None
    resolvedBy: Optional[str] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
