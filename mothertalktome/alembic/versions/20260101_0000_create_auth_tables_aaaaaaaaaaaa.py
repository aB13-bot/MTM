"""create auth tables

Revision ID: aaaaaaaaaaaa
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'aaaaaaaaaaaa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('auth_user',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=256), nullable=False),
    sa.Column('hashed_password', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('bio_memory', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_auth_user_email'), 'auth_user', ['email'], unique=True)

    op.create_table('auth_refresh_token',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('refresh_token', sa.String(length=512), nullable=False),
    sa.Column('used', sa.Boolean(), nullable=False),
    sa.Column('exp', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['auth_user.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auth_refresh_token_refresh_token'), 'auth_refresh_token', ['refresh_token'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_auth_refresh_token_refresh_token'), table_name='auth_refresh_token')
    op.drop_table('auth_refresh_token')
    op.drop_index(op.f('ix_auth_user_email'), table_name='auth_user')
    op.drop_table('auth_user')