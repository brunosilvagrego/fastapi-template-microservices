"""Add items table

Revision ID: 4a512fe08a9f
Revises: ad4d52888664
Create Date: 2026-02-10 20:57:07.516000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a512fe08a9f"
down_revision: str | Sequence[str] | None = "ad4d52888664"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_item_user_id_users"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_item"),
        ),
    )
    op.create_index(op.f("ix_item_id"), "item", ["id"], unique=False)
    op.create_index(op.f("ix_item_title"), "item", ["title"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_item_title"), table_name="item")
    op.drop_index(op.f("ix_item_id"), table_name="item")
    op.drop_table("item")
