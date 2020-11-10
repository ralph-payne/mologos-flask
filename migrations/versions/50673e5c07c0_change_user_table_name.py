"""Change user table name

Revision ID: 50673e5c07c0
Revises: 98b604f896cf
Create Date: 2020-11-09 11:15:22.700157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50673e5c07c0'
down_revision = '98b604f896cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('app_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('location', sa.String(length=64), nullable=True),
    sa.Column('about_me', sa.Text(), nullable=True),
    sa.Column('member_since', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('lng_preferred', sa.String(length=3), nullable=True),
    sa.Column('lng_recent', sa.String(length=3), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_app_user_email'), 'app_user', ['email'], unique=True)
    op.create_index(op.f('ix_app_user_username'), 'app_user', ['username'], unique=True)
    op.drop_index('ix_user_email', table_name='user')
    op.drop_index('ix_user_username', table_name='user')
    op.drop_table('user')
    op.drop_constraint(None, 'user_example', type_='foreignkey')
    op.create_foreign_key(None, 'user_example', 'app_user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user_example', type_='foreignkey')
    op.create_foreign_key(None, 'user_example', 'user', ['user_id'], ['id'])
    op.create_table('user',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=64), nullable=True),
    sa.Column('username', sa.VARCHAR(length=64), nullable=True),
    sa.Column('password_hash', sa.VARCHAR(length=128), nullable=True),
    sa.Column('role_id', sa.INTEGER(), nullable=True),
    sa.Column('name', sa.VARCHAR(length=64), nullable=True),
    sa.Column('location', sa.VARCHAR(length=64), nullable=True),
    sa.Column('about_me', sa.TEXT(), nullable=True),
    sa.Column('member_since', sa.DATETIME(), nullable=True),
    sa.Column('last_seen', sa.DATETIME(), nullable=True),
    sa.Column('confirmed', sa.BOOLEAN(), nullable=True),
    sa.Column('is_admin', sa.BOOLEAN(), nullable=True),
    sa.Column('lng_preferred', sa.VARCHAR(length=3), nullable=True),
    sa.Column('lng_recent', sa.VARCHAR(length=3), nullable=True),
    sa.CheckConstraint('confirmed IN (0, 1)'),
    sa.CheckConstraint('is_admin IN (0, 1)'),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_username', 'user', ['username'], unique=1)
    op.create_index('ix_user_email', 'user', ['email'], unique=1)
    op.drop_index(op.f('ix_app_user_username'), table_name='app_user')
    op.drop_index(op.f('ix_app_user_email'), table_name='app_user')
    op.drop_table('app_user')
    # ### end Alembic commands ###