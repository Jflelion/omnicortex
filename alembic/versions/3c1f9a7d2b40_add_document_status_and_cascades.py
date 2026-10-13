"""add document status and cascade deletes

Revision ID: 3c1f9a7d2b40
Revises: 8e7f88b06e09
Create Date: 2026-10-13 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c1f9a7d2b40'
down_revision: Union[str, Sequence[str], None] = '8e7f88b06e09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'documents',
        sa.Column(
            'status',
            sa.String(length=20),
            nullable=False,
            server_default='processing'
        )
    )
    op.add_column(
        'documents',
        sa.Column('error_message', sa.Text(), nullable=True)
    )

    # Backfill existing documents from what is already stored.
    op.execute(
        """
        UPDATE documents
        SET status = 'failed',
            error_message = 'No extractable text was found. The PDF may be scanned or image-only.'
        WHERE extracted_text IS NULL OR extracted_text = ''
        """
    )
    op.execute(
        """
        UPDATE documents
        SET status = 'ready'
        WHERE status = 'processing'
          AND NOT EXISTS (
              SELECT 1 FROM document_chunks
              WHERE document_chunks.document_id = documents.id
                AND document_chunks.embedding IS NULL
          )
        """
    )
    op.execute(
        """
        UPDATE documents
        SET status = 'failed',
            error_message = 'The embedding service was unavailable. Retry with POST /documents/{id}/reindex.'
        WHERE status = 'processing'
        """
    )

    op.drop_constraint(
        'document_chunks_document_id_fkey',
        'document_chunks',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'document_chunks_document_id_fkey',
        'document_chunks',
        'documents',
        ['document_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.drop_constraint(
        'documents_owner_id_fkey',
        'documents',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'documents_owner_id_fkey',
        'documents',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'documents_owner_id_fkey',
        'documents',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'documents_owner_id_fkey',
        'documents',
        'users',
        ['owner_id'],
        ['id']
    )

    op.drop_constraint(
        'document_chunks_document_id_fkey',
        'document_chunks',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'document_chunks_document_id_fkey',
        'document_chunks',
        'documents',
        ['document_id'],
        ['id']
    )

    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'status')
