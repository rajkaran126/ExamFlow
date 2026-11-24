"""Shift and Shift Statistics Models."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ShiftStatus


class Shift(Base, TimestampMixin):
    __tablename__ = "shifts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[str] = mapped_column(String(50), nullable=True)
    start_time: Mapped[str] = mapped_column(String(50), nullable=True)
    end_time: Mapped[str] = mapped_column(String(50), nullable=True)
    paper_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    answer_key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ShiftStatus.SCHEDULED.value, nullable=False)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="shifts")
    candidates: Mapped[list["Candidate"]] = relationship("Candidate", back_populates="shift")
    statistics: Mapped["ShiftStatistics"] = relationship("ShiftStatistics", back_populates="shift", uselist=False)


class ShiftStatistics(Base, TimestampMixin):
    __tablename__ = "shift_statistics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shifts.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_candidates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    appeared: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mean_score: Mapped[Decimal] = mapped_column(Numeric(20, 10), default=Decimal('0.00'), nullable=False)
    std_dev: Mapped[Decimal] = mapped_column(Numeric(20, 10), default=Decimal('0.00'), nullable=False)
    highest_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    lowest_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    normalisation_factor: Mapped[Decimal] = mapped_column(Numeric(20, 10), default=Decimal('1.00'), nullable=False)
    is_pooled: Mapped[bool] = mapped_column(default=False, nullable=False)

    shift: Mapped["Shift"] = relationship("Shift", back_populates="statistics")
