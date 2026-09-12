"""add users and application ownership

Revision ID: 46cf9be8a88b
Revises: c5e7e74ff069
Create Date: 2026-08-31 20:29:33.947113

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "46cf9be8a88b"
down_revision: Union[str, Sequence[str], None] = "c5e7e74ff069"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.add_column(
        "applications",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_applications_user_id",
        "applications",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_applications_user_id",
        "applications",
        type_="foreignkey",
    )

    op.drop_column(
        "applications",
        "user_id",
    )

    op.drop_table("users")

