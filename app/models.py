from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
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


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    experiences: Mapped[list["Experience"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    educations: Mapped[list["Education"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    skills: Mapped[list["Skill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    certifications: Mapped[list["Certification"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    contact_links: Mapped[list["ContactLink"]] = relationship(back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_profiles_visibility"),
        Index("ix_profiles_owner_visibility", "owner_id", "visibility"),
    )


class ContentRecordMixin(TimestampMixin):
    __abstract__ = True

    profile_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    stable_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)


class Experience(ContentRecordMixin, Base):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employer: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile: Mapped[Profile] = relationship(back_populates="experiences")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_experiences_visibility"),
        ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_experiences_profile_owner"),
        UniqueConstraint("profile_id", "stable_id", name="uq_experiences_profile_stable_id"),
        Index("ix_experiences_profile_order", "profile_id", "display_order", "stable_id"),
    )


class Education(ContentRecordMixin, Base):
    __tablename__ = "educations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile: Mapped[Profile] = relationship(back_populates="educations")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_educations_visibility"),
        ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_educations_profile_owner"),
        UniqueConstraint("profile_id", "stable_id", name="uq_educations_profile_stable_id"),
        Index("ix_educations_profile_order", "profile_id", "display_order", "stable_id"),
    )


class Skill(ContentRecordMixin, Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    profile: Mapped[Profile] = relationship(back_populates="skills")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_skills_visibility"),
        ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_skills_profile_owner"),
        UniqueConstraint("profile_id", "stable_id", name="uq_skills_profile_stable_id"),
        Index("ix_skills_profile_order", "profile_id", "display_order", "stable_id"),
    )


class Certification(ContentRecordMixin, Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile: Mapped[Profile] = relationship(back_populates="certifications")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_certifications_visibility"),
        ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_certifications_profile_owner"),
        UniqueConstraint("profile_id", "stable_id", name="uq_certifications_profile_stable_id"),
        Index("ix_certifications_profile_order", "profile_id", "display_order", "stable_id"),
    )


class ContactLink(ContentRecordMixin, Base):
    __tablename__ = "contact_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    profile: Mapped[Profile] = relationship(back_populates="contact_links")

    __table_args__ = (
        CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_contact_links_visibility"),
        ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_contact_links_profile_owner"),
        UniqueConstraint("profile_id", "stable_id", name="uq_contact_links_profile_stable_id"),
        Index("ix_contact_links_profile_order", "profile_id", "display_order", "stable_id"),
    )
