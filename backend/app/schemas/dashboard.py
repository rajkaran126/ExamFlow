"""Dashboard Stats Schemas."""
from typing import Optional
from pydantic import BaseModel

class ActivityItemSchema(BaseModel):
    id: str
    type: str
    message: str
    timestamp: str

class DashboardStatsSchema(BaseModel):
    totalExaminations: int
    registeredCandidates: int
    evaluatedCandidates: int
    qualifiedCandidates: int
    disqualifiedCandidates: int
    proctoringFlags: int
    evaluationProgress: int
    recentActivity: list[ActivityItemSchema] = []
