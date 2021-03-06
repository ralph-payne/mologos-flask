"""Update user model

Revision ID: fa10592684bc
Revises: aa0242d79da7
Create Date: 2020-08-31 10:58:49.213543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa10592684bc'
down_revision = 'aa0242d79da7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_role_default'), 'role', ['default'], unique=False)
    op.add_column('user', sa.Column('confirmed', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('email', sa.String(length=64), nullable=True))
    op.add_column('user', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_foreign_key(None, 'user', 'role', ['role_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_column('user', 'role_id')
    op.drop_column('user', 'email')
    op.drop_column('user', 'confirmed')
    op.drop_index(op.f('ix_role_default'), table_name='role')
    op.drop_table('role')
    # ### end Alembic commands ###
