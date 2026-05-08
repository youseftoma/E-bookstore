"""add status to order table

Revision ID: f289519899f3
Revises: f2c6ac93e36e
Create Date: 2026-03-26 13:53:59.855989

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f289519899f3'
down_revision: Union[str, Sequence[str], None] = 'f2c6ac93e36e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum type
order_status_enum = sa.Enum(
    'PENDING', 'ORDERED', 'SHIPPED', 'COMPLETED', 'CANCELLED',name='orderstatus')

def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type in the database
    order_status_enum.create(op.get_bind(), checkfirst=True)

    # Add the column using the enum
    op.add_column(
        'orders',
        sa.Column('status', order_status_enum, nullable=False)
    )

def downgrade() -> None:
    """Downgrade schema."""
    # Drop the column
    op.drop_column('orders', 'status')

    # Drop the enum type
    order_status_enum.drop(op.get_bind(), checkfirst=True)



