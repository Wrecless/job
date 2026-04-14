import uuid
from datetime import datetime

from sqlalchemy import DateTime, DECIMAL, ForeignKey, String, UniqueConstraint, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.db.base import Base


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("jobs.id"), nullable=False)
    score_total: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    explanation: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread")
    draft_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_alert_user_job"),)

    user: Mapped["User"] = relationship("User", back_populates="job_alerts")
    job: Mapped["Job"] = relationship("Job", back_populates="alerts")


from backend.db.models.job import Job
from backend.db.models.user import User
