"""Add row num to international accent

Revision ID: 32c977fdaeff
Revises: 4a375b1ce819
Create Date: 2020-11-16 10:07:36.184200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32c977fdaeff'
down_revision = '4a375b1ce819'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('international_accent', sa.Column('row_num', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('international_accent', 'row_num')
    # ### end Alembic commands ###
