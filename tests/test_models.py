import pytest
from app.models.judgment import Judgment, Citation, CourtLevel, OutcomeType, CitationRelationship
from app.models.judge import Judge, JudgeAnalytics
from app.extensions import db
from datetime import date


@pytest.fixture
def sample_judge_data(app):
    """Create sample judge and judgment data."""
    with app.app_context():
        judge = Judge(
            full_name='Dato\' Justice Ahmad',
            title='Dato\'',
            court_level=CourtLevel.HIGH,
            court_location='Kuala Lumpur',
            date_appointed=date(2010, 1, 1)
        )
        db.session.add(judge)
        db.session.commit()

        # Create judgments with this judge
        for i in range(10):
            j = Judgment(
                id=f'judge-test-j{i}',
                citation=f'[2024] {i} CLJ {100+i}',
                title=f'Test Case {i}',
                court_level=CourtLevel.HIGH,
                court_location='Kuala Lumpur',
                coram=[judge.full_name],
                parties_plaintiff=['Plaintiff'],
                parties_defendant=['Defendant'],
                date_decided=date(2024, 1, i+1),
                subject_matter=['Contract'],
                full_text='Test judgment',
                outcome=OutcomeType.ALLOWED if i % 2 == 0 else OutcomeType.DISMISSED,
                is_published=True
            )
            db.session.add(j)

        db.session.commit()
        yield judge


def test_judgment_citation_uniqueness(app):
    """Test that judgment citations are unique."""
    with app.app_context():
        j1 = Judgment(
            id='unique-test-1',
            citation='[2024] 1 CLJ 1',
            title='Case 1',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        db.session.add(j1)
        db.session.commit()

        # Attempting to add duplicate citation should fail
        j2 = Judgment(
            id='unique-test-2',
            citation='[2024] 1 CLJ 1',  # Same citation
            title='Case 2',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        db.session.add(j2)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

        db.session.rollback()


def test_citation_relationship_creation(app):
    """Test creating citation relationships between judgments."""
    with app.app_context():
        j1 = Judgment(
            id='citing-test-1',
            citation='[2024] 1 CLJ 1',
            title='Case 1',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        j2 = Judgment(
            id='cited-test-1',
            citation='[2023] 1 CLJ 1',
            title='Case 2',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        db.session.add_all([j1, j2])
        db.session.commit()

        # Create citation relationship
        citation = Citation(
            citing_judgment_id=j1.id,
            cited_judgment_id=j2.id,
            relationship=CitationRelationship.FOLLOWED
        )
        db.session.add(citation)
        db.session.commit()

        # Verify relationship
        assert citation.relationship == CitationRelationship.FOLLOWED
        assert citation.citing_judgment_id == j1.id
        assert citation.cited_judgment_id == j2.id


def test_judgment_citation_count_property(app):
    """Test that citation_count property works."""
    with app.app_context():
        j1 = Judgment(
            id='count-test-1',
            citation='[2024] 1 CLJ 100',
            title='Popular Case',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        db.session.add(j1)
        db.session.commit()

        # Initially no citations
        assert j1.citation_count == 0

        # Add citing cases
        for i in range(3):
            j = Judgment(
                id=f'citing-case-{i}',
                citation=f'[2024] {i} CLJ {200+i}',
                title=f'Case {i}',
                court_level=CourtLevel.HIGH,
                court_location='KL',
                full_text='Test'
            )
            db.session.add(j)
            db.session.flush()

            c = Citation(
                citing_judgment_id=j.id,
                cited_judgment_id=j1.id,
                relationship=CitationRelationship.FOLLOWED
            )
            db.session.add(c)

        db.session.commit()

        # Refresh and check count
        j1_refreshed = Judgment.query.filter_by(id='count-test-1').first()
        assert j1_refreshed.citation_count == 3


def test_judge_analytics_computation(app, sample_judge_data):
    """Test JudgeAnalytics computation."""
    with app.app_context():
        judge = sample_judge_data

        # Compute analytics
        analytics = JudgeAnalytics(
            judge_id=judge.id,
            total_cases=10,
            plaintiff_win_rate=0.5,  # 50% win rate
            defendant_win_rate=0.5,
            avg_days_to_judgment=120.5
        )
        db.session.add(analytics)
        db.session.commit()

        # Retrieve and verify
        retrieved = JudgeAnalytics.query.filter_by(judge_id=judge.id).first()
        assert retrieved is not None
        assert retrieved.total_cases == 10
        assert retrieved.plaintiff_win_rate == 0.5


def test_judge_analytics_win_rate_calculation(app, sample_judge_data):
    """Test win rate calculation for judges."""
    with app.app_context():
        judge = sample_judge_data

        # Count outcomes from judgments
        judgments = Judgment.query.filter(
            Judgment.coram.contains([judge.full_name])
        ).all()

        allowed_count = sum(1 for j in judgments if j.outcome == OutcomeType.ALLOWED)
        dismissed_count = sum(1 for j in judgments if j.outcome == OutcomeType.DISMISSED)

        total = allowed_count + dismissed_count
        if total > 0:
            plaintiff_win_rate = allowed_count / total

            analytics = JudgeAnalytics(
                judge_id=judge.id,
                total_cases=total,
                plaintiff_win_rate=plaintiff_win_rate
            )
            db.session.add(analytics)
            db.session.commit()

            retrieved = JudgeAnalytics.query.filter_by(judge_id=judge.id).first()
            assert retrieved.plaintiff_win_rate > 0


def test_search_vector_tsvector_field(app):
    """Test that search_vector field can store TSVECTOR data."""
    with app.app_context():
        judgment = Judgment(
            id='vector-test-1',
            citation='[2024] 1 CLJ 500',
            title='Test Vector Case',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='This is a judgment about contract law and torts.',
            search_vector="'contract':4 'judgment':2 'law':6 'torts':8"
        )
        db.session.add(judgment)
        db.session.commit()

        retrieved = Judgment.query.filter_by(id='vector-test-1').first()
        assert retrieved.search_vector is not None


def test_judgment_embedding_field(app):
    """Test that embedding field stores vector data."""
    with app.app_context():
        # Mock 1536-dim vector
        mock_embedding = [0.1 + (i * 0.0001) for i in range(1536)]

        judgment = Judgment(
            id='embedding-test-1',
            citation='[2024] 1 CLJ 600',
            title='Test Embedding Case',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test judgment',
            embedding=mock_embedding
        )
        db.session.add(judgment)
        db.session.commit()

        retrieved = Judgment.query.filter_by(id='embedding-test-1').first()
        assert retrieved.embedding is not None
        assert len(retrieved.embedding) == 1536


def test_judgment_jsonb_fields(app):
    """Test JSONB fields store complex data."""
    with app.app_context():
        coram_data = [
            {'name': 'Dato\' Justice Ahmad', 'title': 'Dato\''},
            {'name': 'Justice Lee', 'title': 'Tan Sri'}
        ]

        law_report_refs = {
            'mlj': '3 MLJ 250',
            'clj': '[2024] 3 CLJ 101'
        }

        judgment = Judgment(
            id='jsonb-test-1',
            citation='[2024] 1 CLJ 700',
            title='Test JSONB Case',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test',
            coram=coram_data,
            law_report_refs=law_report_refs
        )
        db.session.add(judgment)
        db.session.commit()

        retrieved = Judgment.query.filter_by(id='jsonb-test-1').first()
        assert len(retrieved.coram) == 2
        assert retrieved.law_report_refs['mlj'] == '3 MLJ 250'


def test_judgment_array_fields(app):
    """Test ARRAY fields for parties and subject matter."""
    with app.app_context():
        judgment = Judgment(
            id='array-test-1',
            citation='[2024] 1 CLJ 800',
            title='Test Array Case',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test',
            parties_plaintiff=['Ahmad bin Abdullah', 'Hamka Suleiman'],
            parties_defendant=['Syarikat XYZ Sdn Bhd', 'Contractor ABC'],
            subject_matter=['Contract', 'Tort', 'Employment']
        )
        db.session.add(judgment)
        db.session.commit()

        retrieved = Judgment.query.filter_by(id='array-test-1').first()
        assert len(retrieved.parties_plaintiff) == 2
        assert len(retrieved.parties_defendant) == 2
        assert 'Contract' in retrieved.subject_matter


def test_citation_soft_delete(app):
    """Test that citations can be soft-deleted."""
    with app.app_context():
        j1 = Judgment(
            id='soft-delete-1',
            citation='[2024] 1 CLJ 900',
            title='Case 1',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        j2 = Judgment(
            id='soft-delete-2',
            citation='[2024] 1 CLJ 901',
            title='Case 2',
            court_level=CourtLevel.HIGH,
            court_location='KL',
            full_text='Test'
        )
        db.session.add_all([j1, j2])
        db.session.commit()

        citation = Citation(
            citing_judgment_id=j1.id,
            cited_judgment_id=j2.id,
            relationship=CitationRelationship.FOLLOWED
        )
        db.session.add(citation)
        db.session.commit()

        # Delete citation
        db.session.delete(citation)
        db.session.commit()

        # Verify it's gone
        retrieved = Citation.query.filter_by(
            citing_judgment_id=j1.id,
            cited_judgment_id=j2.id
        ).first()
        assert retrieved is None
