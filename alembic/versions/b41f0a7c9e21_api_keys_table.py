"""api keys table

Revision ID: b41f0a7c9e21
Revises: cf876ee82d17
Create Date: 2026-07-18 09:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b41f0a7c9e21'
down_revision: Union[str, Sequence[str], None] = 'cf876ee82d17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'api_keys',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('prefix', sa.String(length=12), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('pk', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.pk']),
        sa.PrimaryKeyConstraint('pk'),
    )
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_keys_id'), ['id'], unique=True)
        batch_op.create_index(batch_op.f('ix_api_keys_pk'), ['pk'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_api_keys_key_hash'), ['key_hash'], unique=True
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_keys_key_hash'))
        batch_op.drop_index(batch_op.f('ix_api_keys_pk'))
        batch_op.drop_index(batch_op.f('ix_api_keys_id'))
    op.drop_table('api_keys')
