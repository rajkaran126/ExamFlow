"""Merit List and Entries."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class MeritList(Base, TimestampMixin):
    __tablename__ = "merit_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="OVERALL", nullable=False)
    generated_at: Mapped[str] = mapped_column(String(50), nullable=True)
    generated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    entries: Mapped[list["MeritListEntry"]] = relationship("MeritListEntry", back_populates="merit_list", cascade="all, delete-orphan", order_by="MeritListEntry.rank")


class MeritListEntry(Base, TimestampMixin):
    __tablename__ = "merit_list_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merit_list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("merit_lists.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    shift_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    category_rank: Mapped[int] = mapped_column(Integer, nullable=True)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    normalised_score: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=True)
    qualification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tie_unresolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allocated_under_gen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    merit_list: Mapped["MeritList"] = relationship("MeritList", back_populates="entries")

    __table_args__ = (
        UniqueConstraint("merit_list_id", "candidate_id", name="uq_merit_list_candidate"),
    )
