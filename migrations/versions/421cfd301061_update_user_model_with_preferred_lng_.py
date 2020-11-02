"""Update user model with preferred lng and recent

Revision ID: 421cfd301061
Revises: a7c25f392658
Create Date: 2020-11-02 11:19:46.182484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '421cfd301061'
down_revision = 'a7c25f392658'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_words_word', table_name='words')
    op.drop_table('words')
    op.drop_table('definitions')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('definitions',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('word', sa.VARCHAR(length=64), nullable=True),
    sa.Column('definition', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['word'], ['words.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('words',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('word', sa.VARCHAR(length=64), nullable=True),
    sa.Column('etymology', sa.TEXT(), nullable=True),
    sa.Column('pronunciation', sa.VARCHAR(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_words_word', 'words', ['word'], unique=1)
    # ### end Alembic commands ###
