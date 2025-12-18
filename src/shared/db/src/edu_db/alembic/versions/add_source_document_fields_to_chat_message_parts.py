"""add_source_document_fields_to_chat_message_parts

Revision ID: add_source_doc_fields
Revises: 6ce0062076e9
Create Date: 2025-12-18 01:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_source_doc_fields'
down_revision: Union[str, Sequence[str], None] = '6ce0062076e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source document fields to chat_message_parts table."""
    op.add_column('chat_message_parts', sa.Column('source_id', sa.String(), nullable=True))
    op.add_column('chat_message_parts', sa.Column('media_type', sa.String(), nullable=True))
    op.add_column('chat_message_parts', sa.Column('source_title', sa.String(), nullable=True))
    op.add_column('chat_message_parts', sa.Column('source_filename', sa.String(), nullable=True))
    op.add_column('chat_message_parts', sa.Column('provider_metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove source document fields from chat_message_parts table."""
    op.drop_column('chat_message_parts', 'provider_metadata')
    op.drop_column('chat_message_parts', 'source_filename')
    op.drop_column('chat_message_parts', 'source_title')
    op.drop_column('chat_message_parts', 'media_type')
    op.drop_column('chat_message_parts', 'source_id')

