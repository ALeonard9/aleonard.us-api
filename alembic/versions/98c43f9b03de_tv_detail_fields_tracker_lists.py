"""tv detail fields + tracker lists

Revision ID: 98c43f9b03de
Revises: 2c4970e2c27f
Create Date: 2026-07-11 14:53:41.295262

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '98c43f9b03de'
down_revision: Union[str, Sequence[str], None] = '2c4970e2c27f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add TVMaze detail columns and Movies-style list flags, then backfill."""
    with op.batch_alter_table('tv_shows', schema=None) as batch_op:
        batch_op.add_column(sa.Column('premiered', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('genre', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('network', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('runtime', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('language', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('rating', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))

    # Add with a server_default so existing rows are populated, then backfill.
    with op.batch_alter_table('user_tv_shows', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'on_watchlist',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                'on_rankings',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))

    # Legacy import: a rank means the show sat on the ranked list; anything
    # tracked without a rank was effectively a watchlist entry.
    op.execute('UPDATE user_tv_shows SET on_rankings = TRUE WHERE rank IS NOT NULL')
    op.execute('UPDATE user_tv_shows SET on_watchlist = TRUE WHERE rank IS NULL')

    # Legacy TV ranks are 0-based (unlike movies); shift affected users to the
    # 1-based positions the rank-placement endpoints assume.
    op.execute(
        'UPDATE user_tv_shows SET rank = rank + 1 WHERE user_id IN ('
        'SELECT user_id FROM user_tv_shows WHERE rank IS NOT NULL '
        'GROUP BY user_id HAVING MIN(rank) = 0)'
    )

    # Drop the server defaults now that existing rows are populated; the app
    # model supplies the default on insert.
    with op.batch_alter_table('user_tv_shows', schema=None) as batch_op:
        batch_op.alter_column('on_watchlist', server_default=None)
        batch_op.alter_column('on_rankings', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user_tv_shows', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('on_rankings')
        batch_op.drop_column('on_watchlist')

    with op.batch_alter_table('tv_shows', schema=None) as batch_op:
        batch_op.drop_column('summary')
        batch_op.drop_column('rating')
        batch_op.drop_column('language')
        batch_op.drop_column('runtime')
        batch_op.drop_column('network')
        batch_op.drop_column('genre')
        batch_op.drop_column('year')
        batch_op.drop_column('premiered')
