"""add stock_counted_at

Records when a quantity was last established, which `updated_at` cannot: that
column moves for a corrected price or a new tag, so it cannot separate a figure
counted this morning from one counted six weeks ago.

The column is nullable and rows already in the table are left NULL, meaning "not
established since this column existed". Backfilling from `updated_at` would date
every legacy row to its last edit of any kind, which is precisely the
overstatement the column exists to remove; backfilling from `created_at` would
invent a count that never happened. A NULL the dashboard can flag for recounting
is the honest answer.

Revision ID: c41a9f2d7b05
Revises: 7e3576b1b6d8
Create Date: 2026-08-18 14:12:03.881204
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'c41a9f2d7b05'
down_revision: str | None = '7e3576b1b6d8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_counted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_column('stock_counted_at')
