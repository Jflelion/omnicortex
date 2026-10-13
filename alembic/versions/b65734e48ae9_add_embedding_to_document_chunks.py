"""add embedding to document chunks

Revision ID: b65734e48ae9
Revises: 6e008703330b
Create Date: 2026-06-11 21:49:43.858150

"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b65734e48ae9'
down_revision: Union[str, Sequence[str], None] = '6e008703330b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE document_chunks
        ALTER COLUMN embedding
        TYPE vector(768);
        """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE document_chunks
        ALTER COLUMN embedding
        TYPE vector(1536);
        """
    )
