"""user visibility settings

Handle + per-category public flags (#143). Everything defaults private;
NULL flags read as private.

Revision ID: d8e3f52a6b14
Revises: c7d2e91b4f03
Create Date: 2026-07-18 11:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd8e3f52a6b14'
down_revision: Union[str, Sequence[str], None] = 'c7d2e91b4f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('handle', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('public_movies', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('public_tv', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('public_books', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('public_games', sa.Boolean(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_handle'), ['handle'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_handle'))
        batch_op.drop_column('public_games')
        batch_op.drop_column('public_books')
        batch_op.drop_column('public_tv')
        batch_op.drop_column('public_movies')
        batch_op.drop_column('handle')
