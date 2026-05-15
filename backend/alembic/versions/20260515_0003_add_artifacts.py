"""add artifacts

Revision ID: 20260515_0003
Revises: 20260515_0002
Create Date: 2026-05-15 15:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260515_0003"
down_revision = "20260515_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id"),
    )
    op.create_index(op.f("ix_artifacts_artifact_id"), "artifacts", ["artifact_id"], unique=True)
    op.create_index(op.f("ix_artifacts_artifact_type"), "artifacts", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_artifacts_created_at"), "artifacts", ["created_at"], unique=False)
    op.create_index(op.f("ix_artifacts_dataset_id"), "artifacts", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_artifacts_deleted_at"), "artifacts", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_artifacts_workspace_id"), "artifacts", ["workspace_id"], unique=False)
    op.create_index("ix_artifacts_storage_key", "artifacts", ["storage_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_artifacts_storage_key", table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_workspace_id"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_deleted_at"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_dataset_id"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_created_at"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_artifact_type"), table_name="artifacts")
    op.drop_index(op.f("ix_artifacts_artifact_id"), table_name="artifacts")
    op.drop_table("artifacts")
