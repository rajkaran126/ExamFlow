"""Answer Key, Versions, Challenges, and Dropped Questions."""
import uuid
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ChallengeStatus, DroppedQuestionScoringRule


class AnswerKey(Base, TimestampMixin):
    __tablename__ = "answer_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examination_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    correct_options: Mapped[list] = mapped_column(JSONB, nullable=False) # list of valid option strings
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    section: Mapped["ExaminationSection"] = relationship("ExaminationSection", back_populates="answer_keys")
    versions: Mapped[list["AnswerKeyVersion"]] = relationship("AnswerKeyVersion", back_populates="answer_key", cascade="all, delete-orphan")
    challenges: Mapped[list["QuestionChallenge"]] = relationship("QuestionChallenge", back_populates="answer_key")

    __table_args__ = (
        UniqueConstraint("examination_id", "section_id", "question_id", "version", name="uq_exam_sec_q_ver"),
    )


class AnswerKeyVersion(Base, TimestampMixin):
    __tablename__ = "answer_key_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answer_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_options: Mapped[list] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    answer_key: Mapped["AnswerKey"] = relationship("AnswerKey", back_populates="versions")


class QuestionChallenge(Base, TimestampMixin):
    __tablename__ = "question_challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("answer_keys.id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_options: Mapped[list] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=ChallengeStatus.PENDING.value, nullable=False)
    decision_note: Mapped[str] = mapped_column(Text, nullable=True)
    decided_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    answer_key: Mapped["AnswerKey"] = relationship("AnswerKey", back_populates="challenges")


class DroppedQuestion(Base, TimestampMixin):
    __tablename__ = "dropped_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examination_sections.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    scoring_rule: Mapped[str] = mapped_column(String(50), default=DroppedQuestionScoringRule.AWARD_ALL.value, nullable=False)
    effective_from_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("examination_id", "section_id", "question_id", name="uq_dropped_q"),
    )
