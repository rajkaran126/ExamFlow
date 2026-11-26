"""Evaluation, Section Results, and Qualification Decisions."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, Numeric, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import QualificationStatus


class EvaluationResult(Base, TimestampMixin):
    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), unique=True, nullable=False)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempted_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    raw_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    total_positive_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    total_negative_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    
    proctoring_penalty_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal('0.00'), nullable=False)
    proctoring_penalty: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False)
    final_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal('0.00'), nullable=False) # raw - penalty
    normalised_score: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=True)
    
    attempt_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal('0.00'), nullable=False)
    qualification_status: Mapped[str] = mapped_column(String(50), default=QualificationStatus.QUALIFIED.value, nullable=False)
    failure_reasons: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evaluated_at: Mapped[str] = mapped_column(String(50), nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="evaluation_result")
    section_results: Mapped[list["SectionResult"]] = relationship("SectionResult", back_populates="evaluation_result", cascade="all, delete-orphan")


class SectionResult(Base, TimestampMixin):
    __tablename__ = "section_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluation_results.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examination_sections.id", ondelete="CASCADE"), nullable=False)
    
    section_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_attempted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    raw_section_score: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    cut_off_applied: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    qualified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    disqualification_reason: Mapped[str] = mapped_column(Text, nullable=True)

    evaluation_result: Mapped["EvaluationResult"] = relationship("EvaluationResult", back_populates="section_results")
