"""add_pgvector_extension

Revision ID: a7213490698e
Revises: 82e63c12156c
Create Date: 2025-09-27 18:49:48.877316

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7213490698e"
down_revision: Union[str, Sequence[str], None] = "82e63c12156c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Update embedding_vector column to use vector type
    op.execute(
        "ALTER TABLE document_segments ALTER COLUMN embedding_vector TYPE vector(1536) USING embedding_vector::vector"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert embedding_vector column to text
    op.execute(
        "ALTER TABLE document_segments ALTER COLUMN embedding_vector TYPE text USING embedding_vector::text"
    )

    # Note: We don't drop the vector extension as it might be used by other tables
