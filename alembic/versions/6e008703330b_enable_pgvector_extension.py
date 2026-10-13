"""enable pgvector extension

Revision ID: 6e008703330b
Revises: aa1bba74d8c7
Create Date: 2026-06-11 21:33:31.606031

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6e008703330b'
down_revision: Union[str, Sequence[str], None] = 'aa1bba74d8c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )


def downgrade() -> None:
    op.execute(
        "DROP EXTENSION IF EXISTS vector"
    )
