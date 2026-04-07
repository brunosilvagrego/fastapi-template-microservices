"""Add clients table

Revision ID: 9efd6b437825
Revises:
Create Date: 2026-04-07 15:43:02.186372

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9efd6b437825"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "clients",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("oauth_id", sa.String(), nullable=False),
        sa.Column("oauth_secret_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clients")),
        sa.UniqueConstraint("oauth_id", name=op.f("uq_clients_oauth_id")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("clients")
