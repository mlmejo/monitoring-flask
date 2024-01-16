"""change default attendance

Revision ID: 3ea26d67fcd7
Revises: 1cbfbfbfcf55
Create Date: 2024-01-16 21:20:04.415554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ea26d67fcd7'
down_revision = '1cbfbfbfcf55'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=64), server_default='Present (incomplete)', nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
