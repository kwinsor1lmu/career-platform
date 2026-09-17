"""Initial resume schema

Revision ID: 0001
Revises:
Create Date: 2026-09-17 21:41:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_profiles_visibility"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profiles_owner_id", "profiles", ["owner_id"], unique=False)
    op.create_index("ix_profiles_owner_visibility", "profiles", ["owner_id", "visibility"], unique=False)
    op.create_index("ix_profiles_visibility", "profiles", ["visibility"], unique=False)

    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("employer", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("start_date", sa.String(length=20), nullable=True),
        sa.Column("end_date", sa.String(length=20), nullable=True),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_experiences_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_experiences_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_experiences_profile_stable_id"),
    )
    op.create_index("ix_experiences_display_order", "experiences", ["display_order"], unique=False)
    op.create_index("ix_experiences_owner_id", "experiences", ["owner_id"], unique=False)
    op.create_index("ix_experiences_profile_id", "experiences", ["profile_id"], unique=False)
    op.create_index("ix_experiences_profile_order", "experiences", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_experiences_stable_id", "experiences", ["stable_id"], unique=False)
    op.create_index("ix_experiences_visibility", "experiences", ["visibility"], unique=False)

    op.create_table(
        "educations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=False),
        sa.Column("degree", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("start_date", sa.String(length=20), nullable=True),
        sa.Column("end_date", sa.String(length=20), nullable=True),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_educations_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_educations_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_educations_profile_stable_id"),
    )
    op.create_index("ix_educations_display_order", "educations", ["display_order"], unique=False)
    op.create_index("ix_educations_owner_id", "educations", ["owner_id"], unique=False)
    op.create_index("ix_educations_profile_id", "educations", ["profile_id"], unique=False)
    op.create_index("ix_educations_profile_order", "educations", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_educations_stable_id", "educations", ["stable_id"], unique=False)
    op.create_index("ix_educations_visibility", "educations", ["visibility"], unique=False)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=80), nullable=True),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_skills_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_skills_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_skills_profile_stable_id"),
    )
    op.create_index("ix_skills_display_order", "skills", ["display_order"], unique=False)
    op.create_index("ix_skills_owner_id", "skills", ["owner_id"], unique=False)
    op.create_index("ix_skills_profile_id", "skills", ["profile_id"], unique=False)
    op.create_index("ix_skills_profile_order", "skills", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_skills_stable_id", "skills", ["stable_id"], unique=False)
    op.create_index("ix_skills_visibility", "skills", ["visibility"], unique=False)

    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("issuer", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("start_date", sa.String(length=20), nullable=True),
        sa.Column("end_date", sa.String(length=20), nullable=True),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_certifications_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_certifications_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_certifications_profile_stable_id"),
    )
    op.create_index("ix_certifications_display_order", "certifications", ["display_order"], unique=False)
    op.create_index("ix_certifications_owner_id", "certifications", ["owner_id"], unique=False)
    op.create_index("ix_certifications_profile_id", "certifications", ["profile_id"], unique=False)
    op.create_index("ix_certifications_profile_order", "certifications", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_certifications_stable_id", "certifications", ["stable_id"], unique=False)
    op.create_index("ix_certifications_visibility", "certifications", ["visibility"], unique=False)

    op.create_table(
        "contact_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_contact_links_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_contact_links_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_contact_links_profile_stable_id"),
    )
    op.create_index("ix_contact_links_display_order", "contact_links", ["display_order"], unique=False)
    op.create_index("ix_contact_links_owner_id", "contact_links", ["owner_id"], unique=False)
    op.create_index("ix_contact_links_profile_id", "contact_links", ["profile_id"], unique=False)
    op.create_index("ix_contact_links_profile_order", "contact_links", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_contact_links_stable_id", "contact_links", ["stable_id"], unique=False)
    op.create_index("ix_contact_links_visibility", "contact_links", ["visibility"], unique=False)


def downgrade() -> None:
    op.drop_table("contact_links")
    op.drop_table("certifications")
    op.drop_table("skills")
    op.drop_table("educations")
    op.drop_table("experiences")
    op.drop_table("profiles")
