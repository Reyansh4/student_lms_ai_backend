"""add_status_column_to_activity

Revision ID: 0abb44e944df
Revises: e06be39f2403
Create Date: 2025-07-01 12:00:54.956004

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0abb44e944df'
down_revision: Union[str, None] = 'e06be39f2403'
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
    
    # Make the column not nullable after setting values
    op.alter_column('activity', 'status', nullable=False)


def downgrade() -> None:
    # Drop the status column
    op.drop_column('activity', 'status')
