"""Add client table

Revision ID: b0f80f919016
Revises:
Create Date: 2026-02-12 02:16:36.214929

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b0f80f919016"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "client",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("oauth_id", sa.String(), nullable=False),
        sa.Column("oauth_secret_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client")),
        sa.UniqueConstraint(
            "oauth_id",
            name=op.f("uq_client_oauth_id"),
        ),
    )
    op.create_index(op.f("ix_client_id"), "client", ["id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_client_id"), table_name="client")
    op.drop_table("client")
