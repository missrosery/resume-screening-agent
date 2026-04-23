import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


JSONType = JSON().with_variant(JSONB(), "postgresql")


class JobPosition(Base):
    __tablename__ = "job_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200))
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    resumes: Mapped[list["Resume"]] = relationship(back_populates="position")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_positions.id"))
    file_name: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str] = mapped_column(String(10))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(20), default="pending")
    parsed_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    position: Mapped[JobPosition] = relationship(back_populates="resumes")


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_positions.id"))
    title: Mapped[str] = mapped_column(String(200), default="New Session")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("screening_sessions.id"),
        nullable=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"))
    match_score: Mapped[int] = mapped_column(Integer)
    match_reasons: Mapped[list[str]] = mapped_column(JSONType)
    weaknesses: Mapped[list[str]] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
