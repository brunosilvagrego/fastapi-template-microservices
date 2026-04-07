"""Add items table

Revision ID: cc3d71af4681
Revises: 9efd6b437825
Create Date: 2026-04-07 15:44:57.765586

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc3d71af4681"
down_revision: str | Sequence[str] | None = "9efd6b437825"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["clients.id"],
            name=op.f("fk_items_owner_id_clients"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_items")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("items")
