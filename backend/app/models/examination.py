"""Examination and Section Models."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ExamStatus


class Examination(Base, TimestampMixin):
    __tablename__ = "examinations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[str] = mapped_column(String(50), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    passing_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ExamStatus.DRAFT.value, nullable=False)
    
    negative_marking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sectional_cutoffs_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    normalisation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    sections: Mapped[list["ExaminationSection"]] = relationship("ExaminationSection", back_populates="examination", cascade="all, delete-orphan", order_by="ExaminationSection.ordering")
    shifts: Mapped[list["Shift"]] = relationship("Shift", back_populates="examination", cascade="all, delete-orphan")
    candidates: Mapped[list["Candidate"]] = relationship("Candidate", back_populates="examination")


class ExaminationSection(Base, TimestampMixin):
    __tablename__ = "examination_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ordering: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    marks_per_correct: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal('1.00'), nullable=False)
    negative_marks_per_wrong: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal('0.25'), nullable=False)
    cut_off_raw: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    cut_off_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal('40.00'), nullable=False)
    category_wise_cutoffs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="sections")
    answer_keys: Mapped[list["AnswerKey"]] = relationship("AnswerKey", back_populates="section")
