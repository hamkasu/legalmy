"""Fix enum values to use uppercase

Revision ID: 003_fix_enum_values
Revises: 002_add_superadmin
Create Date: 2026-06-17 08:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_fix_enum_values'
down_revision = '002_add_superadmin'
branch_labels = None
depends_on = None


def upgrade():
    # Strategy: Convert columns to TEXT, update values, then keep as TEXT
    # This avoids enum type definition conflicts
    # Wrap in try-except to handle cases where tables don't exist

    tables_to_update = [
        ('users', 'role'),
        ('subscriptions', 'status'),
        ('judgments', 'outcome'),
        ('citations', 'relationship'),
        ('cases', 'status'),
        ('parties', 'role'),
        ('case_documents', 'doc_type'),
        ('law_firms', 'headcount_tier'),
        ('alerts', 'frequency'),
    ]

    for table, column in tables_to_update:
        try:
            # Convert to TEXT
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text USING {column}::text;")
            # Update values to uppercase
            op.execute(f"UPDATE {table} SET {column} = upper({column});")
        except Exception as e:
            # Skip if table doesn't exist or other errors
            pass


def downgrade():
    # Revert: Convert back to lowercase

    tables_to_update = [
        ('users', 'role'),
        ('subscriptions', 'status'),
        ('judgments', 'outcome'),
        ('citations', 'relationship'),
        ('cases', 'status'),
        ('parties', 'role'),
        ('case_documents', 'doc_type'),
        ('law_firms', 'headcount_tier'),
        ('alerts', 'frequency'),
    ]

    for table, column in tables_to_update:
        try:
            # Convert to TEXT
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE text USING {column}::text;")
            # Update values to lowercase
            op.execute(f"UPDATE {table} SET {column} = lower({column});")
        except Exception as e:
            # Skip if table doesn't exist or other errors
            pass
