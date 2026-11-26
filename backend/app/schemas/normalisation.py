"""Normalisation Schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ShiftStatisticsSchema(BaseModel):
    shiftId: str
    shiftName: str
    totalCandidates: int
    appeared: int
    meanScore: float
    medianScore: float = 0.0
    standardDeviation: float
    highestScore: float
    lowestScore: float
    normalisationFactor: float

    model_config = ConfigDict(from_attributes=True)
