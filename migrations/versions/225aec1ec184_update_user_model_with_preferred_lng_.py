"""Update user model with preferred lng and recent lng

Revision ID: 225aec1ec184
Revises: aec2aecfad0a
Create Date: 2020-09-21 13:23:35.525115

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '225aec1ec184'
down_revision = 'aec2aecfad0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('lng_preferred', sa.String(length=3), nullable=True))
    op.add_column('user', sa.Column('lng_recent', sa.String(length=3), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'lng_recent')
    op.drop_column('user', 'lng_preferred')
    # ### end Alembic commands ###
