"""Proctoring Event Model."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ProctoringSeverity


class ProctoringEvent(Base, TimestampMixin):
    __tablename__ = "proctoring_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False) # 1 - 10
    severity_level: Mapped[str] = mapped_column(String(50), default=ProctoringSeverity.LOW.value, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(50), nullable=True)
    penalty_applied: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal('0.00'), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_malpractice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="proctoring_events")

    __table_args__ = (
        CheckConstraint("severity >= 1 AND severity <= 10", name="chk_proctoring_severity"),
    )
