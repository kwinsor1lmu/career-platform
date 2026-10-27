"""Add projects table

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26 12:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=120), nullable=False),
        sa.Column("stable_id", sa.String(length=120), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.CheckConstraint("visibility IN ('draft', 'private', 'published')", name="ck_projects_visibility"),
        sa.ForeignKeyConstraint(["profile_id", "owner_id"], ["profiles.id", "profiles.owner_id"], name="fk_projects_profile_owner"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "stable_id", name="uq_projects_profile_stable_id"),
    )
    op.create_index("ix_projects_display_order", "projects", ["display_order"], unique=False)
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)
    op.create_index("ix_projects_profile_id", "projects", ["profile_id"], unique=False)
    op.create_index("ix_projects_profile_order", "projects", ["profile_id", "display_order", "stable_id"], unique=False)
    op.create_index("ix_projects_stable_id", "projects", ["stable_id"], unique=False)
    op.create_index("ix_projects_visibility", "projects", ["visibility"], unique=False)


def downgrade() -> None:
    op.drop_table("projects")
