"""Add sanitized_content to artifacts

Revision ID: 002_add_sanitized_content
Revises: 001_initial_schema
Create Date: 2026-09-15 23:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_sanitized_content'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column
    op.alter_column('artifacts', 'content', new_column_name='raw_content')
    # Add new column
    op.add_column('artifacts', sa.Column('sanitized_content', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('artifacts', 'sanitized_content')
    op.alter_column('artifacts', 'raw_content', new_column_name='content')
