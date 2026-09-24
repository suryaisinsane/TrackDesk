"""add user inbound email

Revision ID: 9c0764f6ba6a
Revises: b29617bd9c65
Create Date: 2026-09-24 18:17:54.970886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c0764f6ba6a'
down_revision: Union[str, Sequence[str], None] = 'b29617bd9c65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Add the column temporarily as nullable.
    op.add_column(
        "users",
        sa.Column(
            "inbound_email",
            sa.String(length=320),
            nullable=True,
        ),
    )

    # 2. Give existing users a unique inbound address.
    op.execute(
        """
        UPDATE users
        SET inbound_email = 'u_' || id || '@inbound.trackdesk.local'
        WHERE inbound_email IS NULL
        """
    )

    # 3. Now that every existing user has a value,
    # make the column required and unique.
    op.alter_column(
        "users",
        "inbound_email",
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_users_inbound_email",
        "users",
        ["inbound_email"],
    )

def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_users_inbound_email",
        "users",
        type_="unique",
    )

    op.drop_column(
        "users",
        "inbound_email",
    )