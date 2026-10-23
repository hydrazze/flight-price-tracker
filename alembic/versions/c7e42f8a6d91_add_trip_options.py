"""Add optional return date and stop preferences to tracks.

Revision ID: c7e42f8a6d91
Revises: 3db07abe68d4
"""
from alembic import op
import sqlalchemy as sa

revision = "c7e42f8a6d91"
down_revision = "3db07abe68d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracks", sa.Column("return_date", sa.Date(), nullable=True))
    op.add_column(
        "tracks",
        sa.Column("stop_preference", sa.String(10), nullable=False, server_default="ANY"),
    )
    op.create_check_constraint(
        "stoppreference", "tracks", "stop_preference IN ('ANY', 'DIRECT', 'WITH_STOPS')"
    )
    op.create_check_constraint(
        "ck_tracks_return_date", "tracks",
        "return_date IS NULL OR return_date >= departure_date",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tracks_return_date", "tracks", type_="check")
    op.drop_constraint("stoppreference", "tracks", type_="check")
    op.drop_column("tracks", "stop_preference")
    op.drop_column("tracks", "return_date")
