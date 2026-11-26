"""Auth Schemas."""
from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatarUrl: Optional[str] = None

class AuthResponse(BaseModel):
    user: UserResponse
    token: str
