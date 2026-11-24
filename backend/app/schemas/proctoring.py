"""Proctoring Schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProctoringEventSchema(BaseModel):
    id: Optional[str] = None
    candidateId: str
    examinationId: str
    eventType: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    timestamp: Optional[str] = None
    penalty: float = 0.0
    evidence: Optional[str] = None
    confirmed: bool = True
    isMalpractice: bool = False

    model_config = ConfigDict(from_attributes=True)
