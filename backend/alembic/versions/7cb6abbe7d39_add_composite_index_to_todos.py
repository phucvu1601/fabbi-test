"""add_composite_index_to_todos

Revision ID: 7cb6abbe7d39
Revises: a0790c76a129
Create Date: 2026-09-17 19:06:08.173124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cb6abbe7d39'
down_revision: Union[str, None] = 'a0790c76a129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a composite index covering user_id, completed, and created_at in descending order.
    op.create_index(
        'idx_todos_user_completed_created',
        'todos',
        ['user_id', 'completed', sa.text('created_at DESC')]
    )


def downgrade() -> None:
    # Drop the index when rolling back the migration.
    op.drop_index('idx_todos_user_completed_created', table_name='todos')