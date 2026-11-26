"""Re-Evaluation Request Model."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ReEvaluationStatus


class ReEvaluationRequest(Base, TimestampMixin):
    __tablename__ = "re_evaluation_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ReEvaluationStatus.PENDING.value, nullable=False)
    original_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    revised_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    requested_at: Mapped[str] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[str] = mapped_column(String(50), nullable=True)
    resolved_by: Mapped[str] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)
