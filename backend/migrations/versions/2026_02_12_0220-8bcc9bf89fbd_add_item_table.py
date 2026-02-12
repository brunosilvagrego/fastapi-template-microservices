"""Add item table

Revision ID: 8bcc9bf89fbd
Revises: b0f80f919016
Create Date: 2026-02-12 02:20:43.047904

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8bcc9bf89fbd"
down_revision: str | Sequence[str] | None = "b0f80f919016"
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
