import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func, Uuid
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_roles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    seniority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    salary_floor: Mapped[int | None] = mapped_column(nullable=True)
    locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    remote_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)
    industries_to_avoid: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    sponsorship_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    company_size_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    keywords_include: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    keywords_exclude: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    locale: Mapped[str] = mapped_column(String(10), default="en")
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

    user: Mapped["User"] = relationship("User", back_populates="profile")


from backend.db.models.user import User
