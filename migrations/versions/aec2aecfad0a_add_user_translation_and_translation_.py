"""Add user_translation and translation tables

Revision ID: aec2aecfad0a
Revises: fa10592684bc
Create Date: 2020-09-01 16:54:33.232604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aec2aecfad0a'
down_revision = 'fa10592684bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('translation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('source_language', sa.String(length=2), nullable=True),
    sa.Column('destination_language', sa.String(length=2), nullable=True),
    sa.Column('input', sa.Text(), nullable=True),
    sa.Column('output', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_translation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('source_language', sa.String(length=2), nullable=True),
    sa.Column('destination_language', sa.String(length=2), nullable=True),
    sa.Column('input', sa.Text(), nullable=True),
    sa.Column('output', sa.Text(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('success', sa.Integer(), nullable=True),
    sa.Column('fail', sa.Integer(), nullable=True),
    sa.Column('skip', sa.Integer(), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('deleted', sa.Boolean(), nullable=True),
    sa.Column('ignored', sa.Boolean(), nullable=True),
    sa.Column('starred', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('user_example', sa.Column('comment', sa.Text(), nullable=True))
    op.add_column('word', sa.Column('created', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('word', 'created')
    op.drop_column('user_example', 'comment')
    op.drop_table('user_translation')
    op.drop_table('translation')
    # ### end Alembic commands ###