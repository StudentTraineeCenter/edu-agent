"""add_page_number_to_document_segments

Revision ID: b8c07ad41090
Revises: 43ddc48af9ac
Create Date: 2025-10-07 19:12:56.158721

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8c07ad41090"
down_revision: Union[str, Sequence[str], None] = "43ddc48af9ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "document_segments", sa.Column("page_number", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("document_segments", "page_number")
