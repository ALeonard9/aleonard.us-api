"""books countries detail fields + tracker lists

Revision ID: 5cfe462a0464
Revises: 98c43f9b03de
Create Date: 2026-07-12 00:17:38.616733

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5cfe462a0464'
down_revision: Union[str, Sequence[str], None] = '98c43f9b03de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_list_flags(table: str) -> None:
    """Add on_watchlist/on_rankings with server defaults for existing rows."""
    with op.batch_alter_table(table, schema=None) as batch_op:
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


def _drop_list_flag_defaults(table: str) -> None:
    """Drop server defaults once existing rows are backfilled."""
    with op.batch_alter_table(table, schema=None) as batch_op:
        batch_op.alter_column('on_watchlist', server_default=None)
        batch_op.alter_column('on_rankings', server_default=None)


def upgrade() -> None:
    """Add detail columns and Movies-style list flags, then backfill."""
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.add_column(sa.Column('authors', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('genre', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('page_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('rating', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('language', sa.String(length=40), nullable=True))

    with op.batch_alter_table('countries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('region', sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column('subregion', sa.String(length=100), nullable=True)
        )
        batch_op.add_column(sa.Column('capital', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('population', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('flag_emoji', sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column('flag_url', sa.String(length=500), nullable=True))

    _add_list_flags('user_books')
    _add_list_flags('user_countries')

    # Books legacy import: completed=1 => read (ranked list, ranks already
    # 1-based); otherwise the to-read pile, whose rank column holds a
    # meaningless 0 sentinel that must not leak into the ranked list.
    op.execute('UPDATE user_books SET on_rankings = TRUE WHERE completed = 1')
    op.execute(
        'UPDATE user_books SET on_watchlist = TRUE '
        'WHERE completed = 0 OR completed IS NULL'
    )
    op.execute('UPDATE user_books SET rank = NULL WHERE on_rankings = FALSE')

    # Countries legacy import: every tracker is a visited country with a
    # 1-based rank; the bucket list starts empty.
    op.execute('UPDATE user_countries SET on_rankings = TRUE WHERE completed = 1')
    op.execute(
        'UPDATE user_countries SET on_watchlist = TRUE '
        'WHERE completed = 0 OR completed IS NULL'
    )
    op.execute('UPDATE user_countries SET rank = NULL WHERE on_rankings = FALSE')

    _drop_list_flag_defaults('user_books')
    _drop_list_flag_defaults('user_countries')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user_countries', schema=None) as batch_op:
        batch_op.drop_column('on_rankings')
        batch_op.drop_column('on_watchlist')

    with op.batch_alter_table('user_books', schema=None) as batch_op:
        batch_op.drop_column('on_rankings')
        batch_op.drop_column('on_watchlist')

    with op.batch_alter_table('countries', schema=None) as batch_op:
        batch_op.drop_column('flag_url')
        batch_op.drop_column('flag_emoji')
        batch_op.drop_column('population')
        batch_op.drop_column('capital')
        batch_op.drop_column('subregion')
        batch_op.drop_column('region')

    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.drop_column('language')
        batch_op.drop_column('rating')
        batch_op.drop_column('page_count')
        batch_op.drop_column('description')
        batch_op.drop_column('genre')
        batch_op.drop_column('year')
        batch_op.drop_column('authors')
