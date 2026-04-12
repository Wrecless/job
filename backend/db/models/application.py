import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, Index, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


APPLICATION_STATUSES = [
    "found",
    "saved",
    "tailoring",
    "ready",
    "submitted",
    "interviewing",
    "rejected",
    "offer",
    "closed",
]


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("jobs.id"),
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("resumes.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    submission_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    notes: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job_application"),
        Index("ix_applications_user_status", "user_id", "status"),
        Index("ix_applications_submitted_at", "submitted_at"),
    )

    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    resume: Mapped["Resume"] = relationship("Resume", back_populates="applications")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="application")
    artifacts: Mapped[list["ApplicationArtifact"]] = relationship("ApplicationArtifact", back_populates="application")


from backend.db.models.user import User
from backend.db.models.job import Job
from backend.db.models.resume import Resume
from backend.db.models.task import Task
from backend.db.models.artifact import ApplicationArtifact
