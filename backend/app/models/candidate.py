"""Candidate Model."""
import uuid
from sqlalchemy import String, Boolean, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import CandidateCategory, Gender, CandidateStatus


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shifts.id"), nullable=False, index=True)
    
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(50), nullable=False)  # YYYY-MM-DD
    gender: Mapped[str] = mapped_column(String(20), default=Gender.OTHER.value, nullable=False)
    category: Mapped[str] = mapped_column(String(20), default=CandidateCategory.GEN.value, nullable=False, index=True)
    is_pwd: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pwd_type: Mapped[str] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=CandidateStatus.REGISTERED.value, nullable=False)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="candidates")
    shift: Mapped["Shift"] = relationship("Shift", back_populates="candidates")
    responses: Mapped[list["CandidateResponse"]] = relationship("CandidateResponse", back_populates="candidate", cascade="all, delete-orphan")
    proctoring_events: Mapped[list["ProctoringEvent"]] = relationship("ProctoringEvent", back_populates="candidate")
    evaluation_result: Mapped["EvaluationResult"] = relationship("EvaluationResult", back_populates="candidate", uselist=False)

    __table_args__ = (
        Index("idx_candidate_exam_category", "examination_id", "category"),
    )
