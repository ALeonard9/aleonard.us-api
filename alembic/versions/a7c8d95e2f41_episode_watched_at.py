"""episode watched_at

When an episode was actually watched (#160): stamped on mark going forward,
restored from orion's ``g_first``/``g_created`` for pre-cutover history by
``app.migration.backfill_orion_timestamps``. The Activity feed orders episode
entries by ``COALESCE(watched_at, updated_at)``.

Revision ID: a7c8d95e2f41
Revises: f2a5b74c8d36
Create Date: 2026-07-19 08:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a7c8d95e2f41'
down_revision: Union[str, Sequence[str], None] = 'f2a5b74c8d36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('user_tv_episodes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('watched_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user_tv_episodes', schema=None) as batch_op:
        batch_op.drop_column('watched_at')
