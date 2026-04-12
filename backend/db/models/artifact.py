import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


ARTIFACT_TYPES = [
    "resume_variant",
    "cover_letter",
    "short_answer",
    "outreach",
    "follow_up",
]


class ApplicationArtifact(Base):
    __tablename__ = "application_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(CHAR(36), primary_key=True)
    application_id: Mapped[uuid.UUID] = mapped_column(
        CHAR(36),
        ForeignKey("applications.id"),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    application: Mapped["Application"] = relationship("Application", back_populates="artifacts")


from backend.db.models.application import Application
