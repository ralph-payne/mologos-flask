"""UserLanguagePreference schema added

Revision ID: c0b598ba2aa9
Revises: be2d2be29631
Create Date: 2020-11-23 09:38:57.795745

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0b598ba2aa9'
down_revision = 'be2d2be29631'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_language_preference',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('english', sa.Boolean(), nullable=True),
    sa.Column('german', sa.Boolean(), nullable=True),
    sa.Column('italian', sa.Boolean(), nullable=True),
    sa.Column('portuguese', sa.Boolean(), nullable=True),
    sa.Column('spanish', sa.Boolean(), nullable=True),
    sa.Column('latin', sa.Boolean(), nullable=True),
    sa.Column('greek', sa.Boolean(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_language_preference_user_id'), 'user_language_preference', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_language_preference_user_id'), table_name='user_language_preference')
    op.drop_table('user_language_preference')
    # ### end Alembic commands ###
