"""Merit List Schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MeritListEntrySchema(BaseModel):
    rank: int
    candidateId: str
    candidateName: str
    rollNumber: str
    category: str
    categoryRank: Optional[int] = None
    totalMarks: float
    normalisedScore: Optional[float] = None
    qualificationStatus: str
    shiftName: Optional[str] = None
    isSelected: bool = False
    tieUnresolved: bool = False

    model_config = ConfigDict(from_attributes=True)
