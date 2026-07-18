"""Add track status

Revision ID: 3db07abe68d4
Revises: 18eae089ade5
Create Date: 2026-07-18 16:27:14.634854
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3db07abe68d4"
down_revision: Union[str, Sequence[str], None] = "18eae089ade5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    track_status = sa.Enum(
        "UNKNOWN",
        "AVAILABLE",
        "NOT_FOUND",
        "ERROR",
        name="trackstatus",
    )

    track_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "tracks",
        sa.Column(
            "status",
            track_status,
            nullable=False,
            server_default="UNKNOWN",
        ),
    )

    op.add_column(
        "tracks",
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.alter_column(
        "tracks",
        "status",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("tracks", "last_checked_at")
    op.drop_column("tracks", "status")

    sa.Enum(
        "UNKNOWN",
        "AVAILABLE",
        "NOT_FOUND",
        "ERROR",
        name="trackstatus",
    ).drop(op.get_bind(), checkfirst=True)