"""Add superadmin user

Revision ID: 002_add_superadmin
Revises: 001_initial_schema
Create Date: 2026-06-17 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_superadmin'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Insert the superadmin user
    op.execute("""
        INSERT INTO users (
            email,
            full_name,
            password_hash,
            role,
            is_active,
            is_verified,
            preferences,
            created_at
        ) VALUES (
            'hamka.suleiman@calmic.com.my',
            'Hamka Suleiman',
            '$2b$12$lM520kbZ5FqSyn35DQddTuX4q.c2EYmIpNms6S2VEPppsznUgS8TS',
            'admin',
            true,
            true,
            '{}',
            NOW()
        ) ON CONFLICT (email) DO UPDATE SET
            role = 'admin',
            is_active = true,
            is_verified = true,
            password_hash = '$2b$12$lM520kbZ5FqSyn35DQddTuX4q.c2EYmIpNms6S2VEPppsznUgS8TS'
    """)


def downgrade():
    # Remove the superadmin user
    op.execute("""
        DELETE FROM users WHERE email = 'hamka.suleiman@calmic.com.my'
    """)
