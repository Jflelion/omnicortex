"""fix embedding dimensions to 768

Revision ID: 8e7f88b06e09
Revises: cd019e29405e
Create Date: 2026-06-18 22:39:00.763030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e7f88b06e09'
down_revision: Union[str, Sequence[str], None] = 'cd019e29405e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
