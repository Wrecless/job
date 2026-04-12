import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, DECIMAL, ForeignKey, UniqueConstraint, Index, func, Uuid
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("jobs.id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    score_total: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("job_id", "user_id", name="uq_job_user_match"),
        Index("ix_match_scores_user_score", "user_id", "score_total"),
    )

    job: Mapped["Job"] = relationship("Job", back_populates="match_scores")
    user: Mapped["User"] = relationship("User", back_populates="match_scores")


from backend.db.models.job import Job
from backend.db.models.user import User
