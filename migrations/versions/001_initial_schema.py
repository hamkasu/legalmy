"""Initial schema with all models

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('free', 'subscriber', 'admin', 'api', name='userrole'), nullable=False),
        sa.Column('bar_number', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('bar_number'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('active', 'cancelled', 'trial', name='subscriptionstatus'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('seats', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'])

    # ApiKeys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
    )
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'])

    # Judgments table
    op.create_table(
        'judgments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('citation', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('court_level', sa.Enum('FEDERAL', 'APPEAL', 'HIGH', 'SESSIONS', 'MAGISTRATE', 'INDUSTRIAL', 'SYARIAH_HIGH', 'SYARIAH_APPEAL', name='courtlevel'), nullable=False),
        sa.Column('court_location', sa.String(length=120), nullable=False),
        sa.Column('coram', sa.JSON(), nullable=False),
        sa.Column('parties_plaintiff', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('parties_defendant', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('date_decided', sa.Date(), nullable=True),
        sa.Column('date_delivered', sa.Date(), nullable=True),
        sa.Column('subject_matter', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=False),
        sa.Column('summary_ai', sa.Text(), nullable=True),
        sa.Column('summary_ai_bm', sa.Text(), nullable=True),
        sa.Column('outcome', sa.Enum('allowed', 'dismissed', 'partly_allowed', 'struck_out', name='outcometype'), nullable=True),
        sa.Column('neutral_citation', sa.String(length=255), nullable=True),
        sa.Column('mlj_citation', sa.String(length=255), nullable=True),
        sa.Column('clj_citation', sa.String(length=255), nullable=True),
        sa.Column('amr_citation', sa.String(length=255), nullable=True),
        sa.Column('mlra_citation', sa.String(length=255), nullable=True),
        sa.Column('law_report_refs', sa.JSON(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('citation'),
    )
    op.create_index(op.f('ix_judgments_citation'), 'judgments', ['citation'], unique=True)
    op.create_index(op.f('ix_judgments_court_level'), 'judgments', ['court_level'])
    op.create_index(op.f('ix_judgments_date_decided'), 'judgments', ['date_decided'])
    op.create_index('ix_judgments_court_date', 'judgments', ['court_level', 'date_decided'])
    op.create_index('ix_judgments_embedding', 'judgments', ['embedding'], postgresql_using='ivfflat', postgresql_with={'opclasses': 'vector_cosine_ops'})

    # Citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('citing_judgment_id', sa.String(length=36), nullable=False),
        sa.Column('cited_judgment_id', sa.String(length=36), nullable=False),
        sa.Column('relationship', sa.Enum('followed', 'distinguished', 'overruled', 'considered', 'referred', 'approved', name='citationrelationship'), nullable=False),
        sa.Column('paragraph_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cited_judgment_id'], ['judgments.id'], ),
        sa.ForeignKeyConstraint(['citing_judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_citations_cited_judgment_id'), 'citations', ['cited_judgment_id'])
    op.create_index(op.f('ix_citations_citing_judgment_id'), 'citations', ['citing_judgment_id'])
    op.create_index('ix_citations_citing', 'citations', ['citing_judgment_id'])
    op.create_index('ix_citations_cited', 'citations', ['cited_judgment_id'])

    # Judges table
    op.create_table(
        'judges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('title', sa.String(length=50), nullable=True),
        sa.Column('court_level', sa.Enum('FEDERAL', 'APPEAL', 'HIGH', 'SESSIONS', 'MAGISTRATE', 'INDUSTRIAL', 'SYARIAH_HIGH', 'SYARIAH_APPEAL', name='courtlevel'), nullable=False),
        sa.Column('court_location', sa.String(length=120), nullable=False),
        sa.Column('date_appointed', sa.Date(), nullable=True),
        sa.Column('date_retired', sa.Date(), nullable=True),
        sa.Column('biography_text', sa.Text(), nullable=True),
        sa.Column('bar_council_id', sa.String(length=50), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bar_council_id'),
    )
    op.create_index(op.f('ix_judges_court_level'), 'judges', ['court_level'])
    op.create_index('ix_judges_court_location', 'judges', ['court_level', 'court_location'])

    # JudgeAnalytics table
    op.create_table(
        'judge_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judge_id', sa.Integer(), nullable=False),
        sa.Column('total_cases', sa.Integer(), nullable=False),
        sa.Column('plaintiff_win_rate', sa.Float(), nullable=True),
        sa.Column('defendant_win_rate', sa.Float(), nullable=True),
        sa.Column('avg_days_to_judgment', sa.Float(), nullable=True),
        sa.Column('subject_matter_breakdown', sa.JSON(), nullable=False),
        sa.Column('motion_grant_rates', sa.JSON(), nullable=False),
        sa.Column('cases_by_year', sa.JSON(), nullable=False),
        sa.Column('cases_by_court_level', sa.JSON(), nullable=False),
        sa.Column('most_cited_statutes', sa.JSON(), nullable=False),
        sa.Column('landmark_judgments', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['judge_id'], ['judges.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('judge_id'),
    )
    op.create_index(op.f('ix_judge_analytics_judge_id'), 'judge_analytics', ['judge_id'], unique=True)

    # LawFirms table
    op.create_table(
        'law_firms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('established_year', sa.Integer(), nullable=True),
        sa.Column('headcount_tier', sa.Enum('solo', 'small', 'medium', 'large', name='headcounttier'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Lawyers table
    op.create_table(
        'lawyers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('bar_council_number', sa.String(length=50), nullable=False),
        sa.Column('firm_id', sa.Integer(), nullable=True),
        sa.Column('call_year', sa.Integer(), nullable=True),
        sa.Column('specialisations', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['firm_id'], ['law_firms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bar_council_number'),
    )
    op.create_index(op.f('ix_lawyers_bar_council_number'), 'lawyers', ['bar_council_number'], unique=True)
    op.create_index(op.f('ix_lawyers_firm_id'), 'lawyers', ['firm_id'])

    # LawyerAnalytics table
    op.create_table(
        'lawyer_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('total_appearances', sa.Integer(), nullable=False),
        sa.Column('win_rate_plaintiff', sa.Float(), nullable=True),
        sa.Column('win_rate_defendant', sa.Float(), nullable=True),
        sa.Column('court_breakdown', sa.JSON(), nullable=False),
        sa.Column('subject_matter_breakdown', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lawyer_id'], ['lawyers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lawyer_id'),
    )
    op.create_index(op.f('ix_lawyer_analytics_lawyer_id'), 'lawyer_analytics', ['lawyer_id'], unique=True)

    # Acts table
    op.create_table(
        'acts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('short_title', sa.String(length=255), nullable=False),
        sa.Column('long_title', sa.String(length=500), nullable=True),
        sa.Column('act_number', sa.String(length=50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('current_in_force_from', sa.Date(), nullable=True),
        sa.Column('repealed_on', sa.Date(), nullable=True),
        sa.Column('category', sa.JSON(), nullable=False),
        sa.Column('full_text_url', sa.String(length=500), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('act_number'),
    )
    op.create_index(op.f('ix_acts_act_number'), 'acts', ['act_number'], unique=True)

    # Sections table
    op.create_table(
        'sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('section_number', sa.String(length=50), nullable=False),
        sa.Column('heading', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['act_id'], ['acts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sections_act_id'), 'sections', ['act_id'])
    op.create_index('ix_sections_act_section', 'sections', ['act_id', 'section_number'])
    op.create_index('ix_sections_embedding', 'sections', ['embedding'], postgresql_using='ivfflat', postgresql_with={'opclasses': 'vector_cosine_ops'})

    # SubLegislations table
    op.create_table(
        'sub_legislations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('act_id', sa.Integer(), nullable=False),
        sa.Column('pu_number', sa.String(length=50), nullable=False),
        sa.Column('type', sa.Enum('PU_A', 'PU_B', name='sublegislationtype'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('gazetted_date', sa.Date(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['act_id'], ['acts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pu_number'),
    )
    op.create_index(op.f('ix_sub_legislations_pu_number'), 'sub_legislations', ['pu_number'], unique=True)
    op.create_index(op.f('ix_sub_legislations_act_id'), 'sub_legislations', ['act_id'])

    # Cases table
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_number', sa.String(length=100), nullable=False),
        sa.Column('court_level', sa.Enum('FEDERAL', 'APPEAL', 'HIGH', 'SESSIONS', 'MAGISTRATE', 'INDUSTRIAL', 'SYARIAH_HIGH', 'SYARIAH_APPEAL', name='courtlevel'), nullable=False),
        sa.Column('court_location', sa.String(length=120), nullable=False),
        sa.Column('filing_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('active', 'decided', 'struck_out', 'settled', name='casestatus'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('judgment_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['judgment_id'], ['judgments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_number'),
    )
    op.create_index(op.f('ix_cases_case_number'), 'cases', ['case_number'], unique=True)
    op.create_index(op.f('ix_cases_court_level'), 'cases', ['court_level'])
    op.create_index('ix_cases_court_filing', 'cases', ['court_level', 'filing_date'])

    # Parties table
    op.create_table(
        'parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('plaintiff', 'defendant', 'intervener', 'appellant', 'respondent', 'claimant', name='partyrole'), nullable=False),
        sa.Column('counsel_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['counsel_id'], ['lawyers.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_parties_case_id'), 'parties', ['case_id'])
    op.create_index(op.f('ix_parties_counsel_id'), 'parties', ['counsel_id'])
    op.create_index('ix_parties_case_role', 'parties', ['case_id', 'role'])

    # CaseDocuments table
    op.create_table(
        'case_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.Enum('statement_of_claim', 'defence', 'affidavit', 'written_submission', 'order', 'judgment', name='documenttype'), nullable=False),
        sa.Column('filed_date', sa.Date(), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('summary_ai', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_case_documents_case_id'), 'case_documents', ['case_id'])
    op.create_index('ix_case_documents_case_type', 'case_documents', ['case_id', 'doc_type'])

    # SavedSearches table
    op.create_table(
        'saved_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('query_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_saved_searches_user_id'), 'saved_searches', ['user_id'])

    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('saved_search_id', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.Enum('daily', 'weekly', name='alertfrequency'), nullable=False),
        sa.Column('last_sent', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('delivery_email', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['saved_search_id'], ['saved_searches.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_alerts_saved_search_id'), 'alerts', ['saved_search_id'])


def downgrade():
    # Drop all tables in reverse order
    op.drop_table('alerts')
    op.drop_table('saved_searches')
    op.drop_table('case_documents')
    op.drop_table('parties')
    op.drop_table('cases')
    op.drop_table('sub_legislations')
    op.drop_table('sections')
    op.drop_table('acts')
    op.drop_table('lawyer_analytics')
    op.drop_table('lawyers')
    op.drop_table('law_firms')
    op.drop_table('judge_analytics')
    op.drop_table('judges')
    op.drop_table('citations')
    op.drop_table('judgments')
    op.drop_table('api_keys')
    op.drop_table('subscriptions')
    op.drop_table('users')

    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
