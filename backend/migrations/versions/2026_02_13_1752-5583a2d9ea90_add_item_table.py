"""Add item table

Revision ID: 5583a2d9ea90
Revises: f6f7aa29e6a5
Create Date: 2026-02-13 17:52:02.181137

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5583a2d9ea90"
down_revision: str | Sequence[str] | None = "f6f7aa29e6a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["client.id"],
            name=op.f("fk_item_owner_id_client"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item")),
    )
    op.create_index(op.f("ix_item_id"), "item", ["id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_item_id"), table_name="item")
    op.drop_table("item")
