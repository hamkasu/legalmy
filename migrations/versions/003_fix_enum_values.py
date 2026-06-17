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
    # Strategy: Convert columns to TEXT, update values, then convert back to ENUM
    # This avoids enum type conflicts

    # 1. users.role
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text;")
    op.execute("UPDATE users SET role = upper(role);")

    # 2. subscriptions.status
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status TYPE text USING status::text;")
    op.execute("UPDATE subscriptions SET status = upper(status);")

    # 3. judgments.outcome
    op.execute("ALTER TABLE judgments ALTER COLUMN outcome TYPE text USING outcome::text;")
    op.execute("UPDATE judgments SET outcome = upper(outcome);")

    # 4. citations.relationship
    op.execute("ALTER TABLE citations ALTER COLUMN relationship TYPE text USING relationship::text;")
    op.execute("UPDATE citations SET relationship = upper(relationship);")

    # 5. cases.status
    op.execute("ALTER TABLE cases ALTER COLUMN status TYPE text USING status::text;")
    op.execute("UPDATE cases SET status = upper(status);")

    # 6. parties.role
    op.execute("ALTER TABLE parties ALTER COLUMN role TYPE text USING role::text;")
    op.execute("UPDATE parties SET role = upper(role);")

    # 7. case_documents.doc_type
    op.execute("ALTER TABLE case_documents ALTER COLUMN doc_type TYPE text USING doc_type::text;")
    op.execute("UPDATE case_documents SET doc_type = upper(doc_type);")

    # 8. law_firms.headcount_tier
    op.execute("ALTER TABLE law_firms ALTER COLUMN headcount_tier TYPE text USING headcount_tier::text;")
    op.execute("UPDATE law_firms SET headcount_tier = upper(headcount_tier);")

    # 9. alerts.frequency
    op.execute("ALTER TABLE alerts ALTER COLUMN frequency TYPE text USING frequency::text;")
    op.execute("UPDATE alerts SET frequency = upper(frequency);")


def downgrade():
    # Revert: Convert back to lowercase

    # 1. users.role
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text;")
    op.execute("UPDATE users SET role = lower(role);")

    # 2. subscriptions.status
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status TYPE text USING status::text;")
    op.execute("UPDATE subscriptions SET status = lower(status);")

    # 3. judgments.outcome
    op.execute("ALTER TABLE judgments ALTER COLUMN outcome TYPE text USING outcome::text;")
    op.execute("UPDATE judgments SET outcome = lower(outcome);")

    # 4. citations.relationship
    op.execute("ALTER TABLE citations ALTER COLUMN relationship TYPE text USING relationship::text;")
    op.execute("UPDATE citations SET relationship = lower(relationship);")

    # 5. cases.status
    op.execute("ALTER TABLE cases ALTER COLUMN status TYPE text USING status::text;")
    op.execute("UPDATE cases SET status = lower(status);")

    # 6. parties.role
    op.execute("ALTER TABLE parties ALTER COLUMN role TYPE text USING role::text;")
    op.execute("UPDATE parties SET role = lower(role);")

    # 7. case_documents.doc_type
    op.execute("ALTER TABLE case_documents ALTER COLUMN doc_type TYPE text USING doc_type::text;")
    op.execute("UPDATE case_documents SET doc_type = lower(doc_type);")

    # 8. law_firms.headcount_tier
    op.execute("ALTER TABLE law_firms ALTER COLUMN headcount_tier TYPE text USING headcount_tier::text;")
    op.execute("UPDATE law_firms SET headcount_tier = lower(headcount_tier);")

    # 9. alerts.frequency
    op.execute("ALTER TABLE alerts ALTER COLUMN frequency TYPE text USING frequency::text;")
    op.execute("UPDATE alerts SET frequency = lower(frequency);")
