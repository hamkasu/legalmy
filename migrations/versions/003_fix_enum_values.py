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
    # Update UserRole enum values from lowercase to uppercase
    # PostgreSQL requires dropping and recreating enum types

    # Drop the default constraint first
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT;")

    # Update existing data first by casting to text, changing values, then back to enum
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE text USING role::text;
    """)

    op.execute("""
        UPDATE users SET role = upper(role);
    """)

    # Drop old enum type
    op.execute("DROP TYPE IF EXISTS userrole CASCADE;")

    # Create new enum type with uppercase values
    op.execute("""
        CREATE TYPE userrole AS ENUM ('FREE', 'SUBSCRIBER', 'ADMIN', 'API');
    """)

    # Convert back to enum
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole USING role::userrole;
    """)

    # Re-add the default constraint
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'FREE';")

    # Update SubscriptionStatus enum values
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status DROP DEFAULT;")

    op.execute("""
        ALTER TABLE subscriptions
        ALTER COLUMN status TYPE text USING status::text;
    """)

    op.execute("""
        UPDATE subscriptions SET status = upper(status);
    """)

    op.execute("DROP TYPE IF EXISTS subscriptionstatus CASCADE;")

    op.execute("""
        CREATE TYPE subscriptionstatus AS ENUM ('ACTIVE', 'CANCELLED', 'TRIAL');
    """)

    op.execute("""
        ALTER TABLE subscriptions
        ALTER COLUMN status TYPE subscriptionstatus USING status::subscriptionstatus;
    """)

    op.execute("ALTER TABLE subscriptions ALTER COLUMN status SET DEFAULT 'TRIAL';")

    # Update OutcomeType enum values
    op.execute("""
        ALTER TABLE judgments
        ALTER COLUMN outcome TYPE text USING outcome::text;
    """)

    op.execute("""
        UPDATE judgments SET outcome = upper(outcome);
    """)

    op.execute("DROP TYPE IF EXISTS outcometype CASCADE;")

    op.execute("""
        CREATE TYPE outcometype AS ENUM ('ALLOWED', 'DISMISSED', 'PARTLY_ALLOWED', 'STRUCK_OUT');
    """)

    op.execute("""
        ALTER TABLE judgments
        ALTER COLUMN outcome TYPE outcometype USING outcome::outcometype;
    """)

    # Update CitationRelationship enum values
    op.execute("""
        ALTER TABLE citations
        ALTER COLUMN relationship TYPE text USING relationship::text;
    """)

    op.execute("""
        UPDATE citations SET relationship = upper(relationship);
    """)

    op.execute("DROP TYPE IF EXISTS citationrelationship CASCADE;")

    op.execute("""
        CREATE TYPE citationrelationship AS ENUM ('FOLLOWED', 'DISTINGUISHED', 'OVERRULED', 'CONSIDERED', 'REFERRED', 'APPROVED');
    """)

    op.execute("""
        ALTER TABLE citations
        ALTER COLUMN relationship TYPE citationrelationship USING relationship::citationrelationship;
    """)

    # Update CaseStatus enum values
    op.execute("""
        ALTER TABLE cases
        ALTER COLUMN status TYPE text USING status::text;
    """)

    op.execute("""
        UPDATE cases SET status = upper(status);
    """)

    op.execute("DROP TYPE IF EXISTS casestatus CASCADE;")

    op.execute("""
        CREATE TYPE casestatus AS ENUM ('ACTIVE', 'DECIDED', 'STRUCK_OUT', 'SETTLED');
    """)

    op.execute("""
        ALTER TABLE cases
        ALTER COLUMN status TYPE casestatus USING status::casestatus;
    """)

    # Update PartyRole enum values
    op.execute("""
        ALTER TABLE parties
        ALTER COLUMN role TYPE text USING role::text;
    """)

    op.execute("""
        UPDATE parties SET role = upper(role);
    """)

    op.execute("DROP TYPE IF EXISTS partyrole CASCADE;")

    op.execute("""
        CREATE TYPE partyrole AS ENUM ('PLAINTIFF', 'DEFENDANT', 'INTERVENER', 'APPELLANT', 'RESPONDENT', 'CLAIMANT');
    """)

    op.execute("""
        ALTER TABLE parties
        ALTER COLUMN role TYPE partyrole USING role::partyrole;
    """)

    # Update DocumentType enum values
    op.execute("""
        ALTER TABLE case_documents
        ALTER COLUMN doc_type TYPE text USING doc_type::text;
    """)

    op.execute("""
        UPDATE case_documents SET doc_type = upper(replace(doc_type, '_', '_'));
    """)

    op.execute("DROP TYPE IF EXISTS documenttype CASCADE;")

    op.execute("""
        CREATE TYPE documenttype AS ENUM ('STATEMENT_OF_CLAIM', 'DEFENCE', 'AFFIDAVIT', 'WRITTEN_SUBMISSION', 'ORDER', 'JUDGMENT');
    """)

    op.execute("""
        ALTER TABLE case_documents
        ALTER COLUMN doc_type TYPE documenttype USING doc_type::documenttype;
    """)

    # Update HeadcountTier enum values
    op.execute("""
        ALTER TABLE law_firms
        ALTER COLUMN headcount_tier TYPE text USING headcount_tier::text;
    """)

    op.execute("""
        UPDATE law_firms SET headcount_tier = upper(headcount_tier);
    """)

    op.execute("DROP TYPE IF EXISTS headcounttier CASCADE;")

    op.execute("""
        CREATE TYPE headcounttier AS ENUM ('SOLO', 'SMALL', 'MEDIUM', 'LARGE');
    """)

    op.execute("""
        ALTER TABLE law_firms
        ALTER COLUMN headcount_tier TYPE headcounttier USING headcount_tier::headcounttier;
    """)

    # Update AlertFrequency enum values
    op.execute("ALTER TABLE alerts ALTER COLUMN frequency DROP DEFAULT;")

    op.execute("""
        ALTER TABLE alerts
        ALTER COLUMN frequency TYPE text USING frequency::text;
    """)

    op.execute("""
        UPDATE alerts SET frequency = upper(frequency);
    """)

    op.execute("DROP TYPE IF EXISTS alertfrequency CASCADE;")

    op.execute("""
        CREATE TYPE alertfrequency AS ENUM ('DAILY', 'WEEKLY');
    """)

    op.execute("""
        ALTER TABLE alerts
        ALTER COLUMN frequency TYPE alertfrequency USING frequency::alertfrequency;
    """)

    op.execute("ALTER TABLE alerts ALTER COLUMN frequency SET DEFAULT 'DAILY';")


def downgrade():
    # Revert enum values back to lowercase - reverse the process

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE text USING role::text;
    """)

    op.execute("""
        UPDATE users SET role = lower(role);
    """)

    op.execute("DROP TYPE IF EXISTS userrole CASCADE;")

    op.execute("""
        CREATE TYPE userrole AS ENUM ('free', 'subscriber', 'admin', 'api');
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole USING role::userrole;
    """)

    # Similar process for other enums...
    op.execute("""
        ALTER TABLE subscriptions
        ALTER COLUMN status TYPE text USING status::text;
    """)

    op.execute("""
        UPDATE subscriptions SET status = lower(status);
    """)

    op.execute("DROP TYPE IF EXISTS subscriptionstatus CASCADE;")

    op.execute("""
        CREATE TYPE subscriptionstatus AS ENUM ('active', 'cancelled', 'trial');
    """)

    op.execute("""
        ALTER TABLE subscriptions
        ALTER COLUMN status TYPE subscriptionstatus USING status::subscriptionstatus;
    """)
