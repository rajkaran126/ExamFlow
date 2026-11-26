"""Candidate Schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class CandidateSchema(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    rollNumber: str
    registrationNumber: str
    category: str
    isPwD: bool = False
    pwdType: Optional[str] = None
    dateOfBirth: str
    gender: str = "OTHER"
    photoUrl: Optional[str] = None
    examinationId: str
    shiftId: str
    status: str = "REGISTERED"

    model_config = ConfigDict(from_attributes=True)
