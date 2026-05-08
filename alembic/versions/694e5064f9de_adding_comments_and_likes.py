"""adding comments and likes

Revision ID: 694e5064f9de
Revises: f289519899f3
Create Date: 2026-04-05 19:16:58.328613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '694e5064f9de'
down_revision: Union[str, Sequence[str], None] = 'f289519899f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
