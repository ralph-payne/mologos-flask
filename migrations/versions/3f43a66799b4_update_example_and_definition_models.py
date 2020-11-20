"""Update Example and Definition models

Revision ID: 3f43a66799b4
Revises: 50673e5c07c0
Create Date: 2020-11-13 07:39:49.215416

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f43a66799b4'
down_revision = '50673e5c07c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('definition', sa.Column('created', sa.DateTime(), nullable=True))
    op.add_column('definition', sa.Column('word_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'definition', 'word', ['word_id'], ['id'])
    op.drop_column('definition', 'word')
    op.add_column('dictionary_example', sa.Column('word_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'dictionary_example', 'word', ['word_id'], ['id'])
    op.drop_column('dictionary_example', 'word')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dictionary_example', sa.Column('word', sa.VARCHAR(), nullable=True))
    op.drop_constraint(None, 'dictionary_example', type_='foreignkey')
    op.drop_column('dictionary_example', 'word_id')
    op.add_column('definition', sa.Column('word', sa.VARCHAR(), nullable=True))
    op.drop_constraint(None, 'definition', type_='foreignkey')
    op.drop_column('definition', 'word_id')
    op.drop_column('definition', 'created')
    # ### end Alembic commands ###