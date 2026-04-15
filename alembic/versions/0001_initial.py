"""Initial schema — users and itineraries

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("preferences", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "itineraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("num_days", sa.Integer(), nullable=False),
        sa.Column("budget_usd", sa.Float(), nullable=False),
        sa.Column("total_cost_usd", sa.Float(), nullable=False),
        sa.Column("travel_style", sa.String(50), nullable=True),
        sa.Column("itinerary_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("weather_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("itineraries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
