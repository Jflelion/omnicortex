"""fix embedding dimensions to 768

Revision ID: cd019e29405e
Revises: ff9c89228288
Create Date: 2026-06-18 22:28:21.233950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd019e29405e'
down_revision: Union[str, Sequence[str], None] = 'ff9c89228288'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
