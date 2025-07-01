"""add_status_column_to_activity

Revision ID: 4454065354d5
Revises: 0abb44e944df
Create Date: 2025-07-01 12:36:10.705132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4454065354d5'
down_revision: Union[str, None] = '0abb44e944df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the status column as a string first
    op.add_column('activity', sa.Column('status', sa.String(20), nullable=True))
    
    # Update existing activities based on the business logic
    op.execute("""
        UPDATE activity 
        SET status = CASE 
            WHEN is_active = false THEN 'deactive'
            WHEN final_description IS NULL OR final_description = '' THEN 'pending'
            ELSE 'active'
        END
    """)


def downgrade() -> None:
    # Drop the status column
    op.drop_column('activity', 'status')
