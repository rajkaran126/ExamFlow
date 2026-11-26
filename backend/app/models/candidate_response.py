"""Candidate Response Model."""
import uuid
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ResponseStatus


class CandidateResponse(Base, TimestampMixin):
    __tablename__ = "candidate_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examination_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    selected_option: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=ResponseStatus.NOT_ATTEMPTED.value, nullable=False)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # seconds
    response_time: Mapped[str] = mapped_column(String(50), nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("candidate_id", "section_id", "question_id", name="uq_candidate_section_question"),
    )
