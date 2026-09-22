import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    created_at = Column(DateTime, default=lambda: dt.datetime.now(dt.UTC), nullable=False)

    skills = relationship("Skill", back_populates="owner", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="owner", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="owner", cascade="all, delete-orphan")


class Skill(Base):
    """A single skill in a user's profile, with a self-reported/derived proficiency 0-1."""

    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_skill_owner_name"),
        CheckConstraint("level >= 0 AND level <= 1", name="ck_skill_level_range"),
        Index("ix_skills_owner_id", "owner_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    level = Column(Float, default=0.5, nullable=False)
    category = Column(String(60), default="general", nullable=False)

    owner = relationship("User", back_populates="skills")


class Scan(Base):
    """A single job-posting scan result, persisted for history/re-scoring."""

    __tablename__ = "scans"
    __table_args__ = (
        Index("ix_scans_owner_created", "owner_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_text = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    matched_skills = Column(Text, default="")
    gap_skills = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: dt.datetime.now(dt.UTC), nullable=False)

    owner = relationship("User", back_populates="scans")


class Application(Base):
    """A tracked job application, optionally linked back to the scan that produced it."""

    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_owner_created", "owner_id", "created_at"),
        CheckConstraint(
            "status IN ('applied','interview','offer','rejected')", name="ck_application_status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(200), nullable=False)
    role_title = Column(String(200), nullable=False)
    status = Column(String(20), default="applied", nullable=False)
    match_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: dt.datetime.now(dt.UTC), nullable=False)

    owner = relationship("User", back_populates="applications")
