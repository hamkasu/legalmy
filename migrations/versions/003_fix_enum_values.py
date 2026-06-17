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
    # Simple approach: just update the data values in place
    # The enum types already accept both uppercase and lowercase values initially
    # We just need to change what's stored to match the new model expectations

    # These are the enum value conversions needed:
    # users.role: 'admin' -> 'ADMIN', 'free' -> 'FREE', etc.
    # subscriptions.status: 'active' -> 'ACTIVE', etc.
    # And similar for other enum columns

    # Start a transaction for all updates
    updates = [
        # users table
        ("UPDATE users SET role = 'ADMIN' WHERE role = 'admin';", "users.role"),
        ("UPDATE users SET role = 'FREE' WHERE role = 'free';", "users.role"),
        ("UPDATE users SET role = 'SUBSCRIBER' WHERE role = 'subscriber';", "users.role"),
        ("UPDATE users SET role = 'API' WHERE role = 'api';", "users.role"),

        # subscriptions table
        ("UPDATE subscriptions SET status = 'ACTIVE' WHERE status = 'active';", "subscriptions.status"),
        ("UPDATE subscriptions SET status = 'CANCELLED' WHERE status = 'cancelled';", "subscriptions.status"),
        ("UPDATE subscriptions SET status = 'TRIAL' WHERE status = 'trial';", "subscriptions.status"),

        # judgments table
        ("UPDATE judgments SET outcome = 'ALLOWED' WHERE outcome = 'allowed';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'DISMISSED' WHERE outcome = 'dismissed';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'PARTLY_ALLOWED' WHERE outcome = 'partly_allowed';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'STRUCK_OUT' WHERE outcome = 'struck_out';", "judgments.outcome"),

        # citations table
        ("UPDATE citations SET relationship = 'FOLLOWED' WHERE relationship = 'followed';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'DISTINGUISHED' WHERE relationship = 'distinguished';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'OVERRULED' WHERE relationship = 'overruled';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'CONSIDERED' WHERE relationship = 'considered';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'REFERRED' WHERE relationship = 'referred';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'APPROVED' WHERE relationship = 'approved';", "citations.relationship"),

        # cases table
        ("UPDATE cases SET status = 'ACTIVE' WHERE status = 'active';", "cases.status"),
        ("UPDATE cases SET status = 'DECIDED' WHERE status = 'decided';", "cases.status"),
        ("UPDATE cases SET status = 'STRUCK_OUT' WHERE status = 'struck_out';", "cases.status"),
        ("UPDATE cases SET status = 'SETTLED' WHERE status = 'settled';", "cases.status"),

        # parties table
        ("UPDATE parties SET role = 'PLAINTIFF' WHERE role = 'plaintiff';", "parties.role"),
        ("UPDATE parties SET role = 'DEFENDANT' WHERE role = 'defendant';", "parties.role"),
        ("UPDATE parties SET role = 'INTERVENER' WHERE role = 'intervener';", "parties.role"),
        ("UPDATE parties SET role = 'APPELLANT' WHERE role = 'appellant';", "parties.role"),
        ("UPDATE parties SET role = 'RESPONDENT' WHERE role = 'respondent';", "parties.role"),
        ("UPDATE parties SET role = 'CLAIMANT' WHERE role = 'claimant';", "parties.role"),

        # case_documents table
        ("UPDATE case_documents SET doc_type = 'STATEMENT_OF_CLAIM' WHERE doc_type = 'statement_of_claim';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'DEFENCE' WHERE doc_type = 'defence';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'AFFIDAVIT' WHERE doc_type = 'affidavit';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'WRITTEN_SUBMISSION' WHERE doc_type = 'written_submission';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'ORDER' WHERE doc_type = 'order';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'JUDGMENT' WHERE doc_type = 'judgment';", "case_documents.doc_type"),

        # law_firms table
        ("UPDATE law_firms SET headcount_tier = 'SOLO' WHERE headcount_tier = 'solo';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'SMALL' WHERE headcount_tier = 'small';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'MEDIUM' WHERE headcount_tier = 'medium';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'LARGE' WHERE headcount_tier = 'large';", "law_firms.headcount_tier"),

        # alerts table
        ("UPDATE alerts SET frequency = 'DAILY' WHERE frequency = 'daily';", "alerts.frequency"),
        ("UPDATE alerts SET frequency = 'WEEKLY' WHERE frequency = 'weekly';", "alerts.frequency"),
    ]

    for sql, description in updates:
        try:
            op.execute(sql)
        except Exception as e:
            # Ignore errors for individual updates (table might not exist yet or already updated)
            pass


def downgrade():
    # Revert updates back to lowercase
    updates = [
        ("UPDATE users SET role = 'admin' WHERE role = 'ADMIN';", "users.role"),
        ("UPDATE users SET role = 'free' WHERE role = 'FREE';", "users.role"),
        ("UPDATE users SET role = 'subscriber' WHERE role = 'SUBSCRIBER';", "users.role"),
        ("UPDATE users SET role = 'api' WHERE role = 'API';", "users.role"),

        ("UPDATE subscriptions SET status = 'active' WHERE status = 'ACTIVE';", "subscriptions.status"),
        ("UPDATE subscriptions SET status = 'cancelled' WHERE status = 'CANCELLED';", "subscriptions.status"),
        ("UPDATE subscriptions SET status = 'trial' WHERE status = 'TRIAL';", "subscriptions.status"),

        ("UPDATE judgments SET outcome = 'allowed' WHERE outcome = 'ALLOWED';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'dismissed' WHERE outcome = 'DISMISSED';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'partly_allowed' WHERE outcome = 'PARTLY_ALLOWED';", "judgments.outcome"),
        ("UPDATE judgments SET outcome = 'struck_out' WHERE outcome = 'STRUCK_OUT';", "judgments.outcome"),

        ("UPDATE citations SET relationship = 'followed' WHERE relationship = 'FOLLOWED';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'distinguished' WHERE relationship = 'DISTINGUISHED';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'overruled' WHERE relationship = 'OVERRULED';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'considered' WHERE relationship = 'CONSIDERED';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'referred' WHERE relationship = 'REFERRED';", "citations.relationship"),
        ("UPDATE citations SET relationship = 'approved' WHERE relationship = 'APPROVED';", "citations.relationship"),

        ("UPDATE cases SET status = 'active' WHERE status = 'ACTIVE';", "cases.status"),
        ("UPDATE cases SET status = 'decided' WHERE status = 'DECIDED';", "cases.status"),
        ("UPDATE cases SET status = 'struck_out' WHERE status = 'STRUCK_OUT';", "cases.status"),
        ("UPDATE cases SET status = 'settled' WHERE status = 'SETTLED';", "cases.status"),

        ("UPDATE parties SET role = 'plaintiff' WHERE role = 'PLAINTIFF';", "parties.role"),
        ("UPDATE parties SET role = 'defendant' WHERE role = 'DEFENDANT';", "parties.role"),
        ("UPDATE parties SET role = 'intervener' WHERE role = 'INTERVENER';", "parties.role"),
        ("UPDATE parties SET role = 'appellant' WHERE role = 'APPELLANT';", "parties.role"),
        ("UPDATE parties SET role = 'respondent' WHERE role = 'RESPONDENT';", "parties.role"),
        ("UPDATE parties SET role = 'claimant' WHERE role = 'CLAIMANT';", "parties.role"),

        ("UPDATE case_documents SET doc_type = 'statement_of_claim' WHERE doc_type = 'STATEMENT_OF_CLAIM';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'defence' WHERE doc_type = 'DEFENCE';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'affidavit' WHERE doc_type = 'AFFIDAVIT';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'written_submission' WHERE doc_type = 'WRITTEN_SUBMISSION';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'order' WHERE doc_type = 'ORDER';", "case_documents.doc_type"),
        ("UPDATE case_documents SET doc_type = 'judgment' WHERE doc_type = 'JUDGMENT';", "case_documents.doc_type"),

        ("UPDATE law_firms SET headcount_tier = 'solo' WHERE headcount_tier = 'SOLO';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'small' WHERE headcount_tier = 'SMALL';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'medium' WHERE headcount_tier = 'MEDIUM';", "law_firms.headcount_tier"),
        ("UPDATE law_firms SET headcount_tier = 'large' WHERE headcount_tier = 'LARGE';", "law_firms.headcount_tier"),

        ("UPDATE alerts SET frequency = 'daily' WHERE frequency = 'DAILY';", "alerts.frequency"),
        ("UPDATE alerts SET frequency = 'weekly' WHERE frequency = 'WEEKLY';", "alerts.frequency"),
    ]

    for sql, description in updates:
        try:
            op.execute(sql)
        except Exception as e:
            # Ignore errors for individual updates
            pass
