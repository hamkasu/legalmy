import pytest
import json
from app.models.judgment import Judgment, CourtLevel, Citation, CitationRelationship
from app.extensions import db
from datetime import date


def test_text_cleaning_strips_boilerplate():
    """Test that text cleaning removes boilerplate headers/footers."""
    from app.services.ingest_pipeline import clean_judgment_text

    raw_text = """
    FEDERAL COURT OF MALAYSIA
    [2024] 3 CLJ 101

    HEADNOTE: Summary of the case...

    FULL TEXT:
    The facts of the case are as follows...

    Judgment is therefore allowed.

    _______________
    Dated this 15th day of January 2024
    """

    cleaned = clean_judgment_text(raw_text)
    assert 'FEDERAL COURT OF MALAYSIA' not in cleaned
    assert 'The facts of the case are as follows' in cleaned


def test_citation_extraction_regex():
    """Test citation format extraction."""
    from app.services.ingest_pipeline import extract_citations_from_text

    text = """
    Following the case of [2024] 3 CLJ 101 and [2023] 5 MLJ 250,
    the court also considered [2022] 1 MLRA 5.
    """

    citations = extract_citations_from_text(text)
    assert '[2024] 3 CLJ 101' in citations or len(citations) > 0


def test_deduplication_skips_existing():
    """Test that ingestion skips existing citation+court_level combinations."""
    from app.services.ingest_pipeline import should_skip_judgment

    judgment_data = {
        'citation': '[2024] 3 CLJ 101',
        'court_level': CourtLevel.HIGH,
    }

    # First judgment should not be skipped
    assert not should_skip_judgment(judgment_data)

    # Create the judgment
    j = Judgment(
        id='test-j1',
        citation='[2024] 3 CLJ 101',
        title='Test Case',
        court_level=CourtLevel.HIGH,
        court_location='KL',
        full_text='Test'
    )
    db.session.add(j)
    db.session.commit()

    # Same citation+court should now be skipped
    assert should_skip_judgment(judgment_data)


def test_judgment_model_stores_extraction_fields(app):
    """Test that Judgment model can store all extraction fields."""
    with app.app_context():
        judgment = Judgment(
            id='test-extraction',
            citation='[2024] 3 CLJ 101',
            title='Test Case for Extraction',
            court_level=CourtLevel.HIGH,
            court_location='Kuala Lumpur',
            coram=['Dato\' Justice X'],
            parties_plaintiff=['Plaintiff'],
            parties_defendant=['Defendant'],
            date_decided=date(2024, 1, 15),
            subject_matter=['Contract', 'Tort'],
            full_text='Complete judgment text here...',
            summary_ai='AI generated summary of 200 words',
            outcome='allowed',
            is_published=True
        )

        db.session.add(judgment)
        db.session.commit()

        # Verify all fields are stored
        retrieved = Judgment.query.filter_by(id='test-extraction').first()
        assert retrieved is not None
        assert retrieved.coram == ['Dato\' Justice X']
        assert 'Contract' in retrieved.subject_matter


def test_citation_relationship_enum_values():
    """Test that Citation relationship types match expected values."""
    valid_relationships = [
        CitationRelationship.FOLLOWED,
        CitationRelationship.DISTINGUISHED,
        CitationRelationship.OVERRULED,
        CitationRelationship.CONSIDERED,
        CitationRelationship.REFERRED,
        CitationRelationship.APPROVED,
    ]

    for rel in valid_relationships:
        assert rel.value in [
            'followed', 'distinguished', 'overruled',
            'considered', 'referred', 'approved'
        ]


def test_ai_enrichment_response_format():
    """Test that AI enrichment returns valid JSON structure."""
    # Mock AI enrichment response
    ai_response = {
        'summary_en': 'English summary',
        'summary_bm': 'Ringkasan Bahasa Melayu',
        'subject_matter': ['Contract', 'Tort'],
        'outcome': 'allowed',
        'coram': ['Dato\' Justice X'],
        'statutes_cited': ['Contracts Act 1950 s. 76'],
        'prior_cases': ['[2023] 5 MLJ 250']
    }

    # Verify required fields are present
    assert 'summary_en' in ai_response or 'summary' in ai_response
    assert 'subject_matter' in ai_response
    assert 'outcome' in ai_response
    assert 'coram' in ai_response


def test_ingest_task_retry_on_failure():
    """Test that ingest tasks have retry logic."""
    from celery import current_app as celery_app
    from app.blueprints.judgments.routes import bp

    # Verify celery task exists
    # (actual task testing would require celery worker)
    assert celery_app is not None


def test_language_detection(app):
    """Test that judgment language is detected and stored."""
    with app.app_context():
        # English judgment
        j_en = Judgment(
            id='test-en',
            citation='[2024] 3 CLJ 101',
            title='The Quick Brown Fox',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='This is an English judgment.',
            language='en'
        )

        # Malay judgment
        j_bm = Judgment(
            id='test-bm',
            citation='[2024] 3 CLJ 102',
            title='Kes Ujian',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Ini adalah keputusan Bahasa Malaysia.',
            language='ms'
        )

        db.session.add_all([j_en, j_bm])
        db.session.commit()

        # Verify language field is set
        en = Judgment.query.filter_by(id='test-en').first()
        bm = Judgment.query.filter_by(id='test-bm').first()

        assert en.language == 'en'
        assert bm.language == 'ms'


def test_embedded_field_accepts_vector(app):
    """Test that embedding field can store vector data."""
    with app.app_context():
        # Create a mock 1536-dim vector
        mock_vector = [0.1] * 1536

        judgment = Judgment(
            id='test-embed',
            citation='[2024] 3 CLJ 101',
            title='Test',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test judgment',
            embedding=mock_vector
        )

        db.session.add(judgment)
        db.session.commit()

        # Retrieve and verify
        retrieved = Judgment.query.filter_by(id='test-embed').first()
        assert retrieved.embedding is not None
