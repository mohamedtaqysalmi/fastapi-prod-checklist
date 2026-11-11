"""Initial schema placeholder.

Revision ID: 20261111_0001
Revises:
Create Date: 2026-11-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261111_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Template ships one revision so `alembic upgrade head` is a real command.
    # Replace this table with your own models under app.db.Base.metadata.
    op.create_table(
        "health_probe",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("note", sa.String(length=64), nullable=False, server_default="ok"),
    )


def downgrade() -> None:
    op.drop_table("health_probe")
