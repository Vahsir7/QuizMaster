"""removed published

Revision ID: ef2500c9bac2
Revises: e57a0d1df38f
Create Date: 2025-03-28 23:40:45.858089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef2500c9bac2'
down_revision = 'e57a0d1df38f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('exam', schema=None) as batch_op:
        batch_op.drop_column('Published')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('exam', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Published', sa.VARCHAR(length=50), nullable=True))

    # ### end Alembic commands ###
