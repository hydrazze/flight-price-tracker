"""Store details of the last selected flight offer.

Revision ID: f284e1a67c30
Revises: c7e42f8a6d91
"""
from alembic import op
import sqlalchemy as sa

revision = "f284e1a67c30"
down_revision = "c7e42f8a6d91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracks", sa.Column("last_offer", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("tracks", "last_offer")
