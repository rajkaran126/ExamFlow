"""Common API Schemas."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: Optional[str] = None
    success: bool = True

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    pageSize: int
    totalPages: int

class ApiError(BaseModel):
    message: str
    code: str
    status: int
    details: Optional[dict[str, list[str]]] = None
