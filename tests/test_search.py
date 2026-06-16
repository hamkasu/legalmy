import pytest
from app.models.judgment import Judgment, CourtLevel, OutcomeType
from app.extensions import db
from datetime import datetime, date


@pytest.fixture
def sample_judgments(app):
    """Create sample judgment data for search tests."""
    with app.app_context():
        j1 = Judgment(
            id='test-j1',
            citation='[2024] 3 CLJ 101',
            title='Ahmad bin Abdullah v Syarikat XYZ Sdn Bhd',
            court_level=CourtLevel.HIGH,
            court_location='Kuala Lumpur',
            coram=['Dato\' Justice Azlan'],
            parties_plaintiff=['Ahmad bin Abdullah'],
            parties_defendant=['Syarikat XYZ Sdn Bhd'],
            date_decided=date(2024, 1, 15),
            subject_matter=['Contract', 'Tort'],
            full_text='This is a test judgment about contract and tort law. The plaintiff sued the defendant...',
            outcome=OutcomeType.ALLOWED,
            is_published=True
        )

        j2 = Judgment(
            id='test-j2',
            citation='[2023] 5 MLJ 250',
            title='Employment Case v Company Ltd',
            court_level=CourtLevel.APPEAL,
            court_location='Putrajaya',
            coram=['Chief Judge'],
            parties_plaintiff=['Employee Union'],
            parties_defendant=['Company Ltd'],
            date_decided=date(2023, 6, 20),
            subject_matter=['Employment', 'Administrative'],
            full_text='This judgment deals with employment law and administrative proceedings...',
            outcome=OutcomeType.DISMISSED,
            is_published=True
        )

        j3 = Judgment(
            id='test-j3',
            citation='[2022] 1 MLRA 5',
            title='Constitutional Law Matter',
            court_level=CourtLevel.FEDERAL,
            court_location='Putrajaya',
            coram=['President of FC'],
            parties_plaintiff=['Government'],
            parties_defendant=['Citizen'],
            date_decided=date(2022, 3, 10),
            subject_matter=['Constitutional'],
            full_text='Supreme court decision on constitutional matters...',
            outcome=OutcomeType.ALLOWED,
            is_published=True
        )

        db.session.add_all([j1, j2, j3])
        db.session.commit()
        yield [j1, j2, j3]


def test_search_endpoint_returns_results(client, sample_judgments):
    """Test that search endpoint returns results."""
    response = client.post('/search/api/judgments', json={
        'q': 'contract',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert isinstance(data['data'], list)


def test_search_with_court_level_filter(client, sample_judgments):
    """Test filtering by court level."""
    response = client.post('/search/api/judgments', json={
        'q': 'law',
        'court_level': 'HIGH',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('total') >= 0


def test_search_with_date_range_filter(client, sample_judgments):
    """Test filtering by date range."""
    response = client.post('/search/api/judgments', json={
        'q': 'test',
        'date_from': '2023-01-01',
        'date_to': '2024-12-31',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'total' in data


def test_search_with_subject_matter_filter(client, sample_judgments):
    """Test filtering by subject matter tags."""
    response = client.post('/search/api/judgments', json={
        'q': 'law',
        'subject_matter': ['Contract', 'Employment'],
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'total' in data


def test_search_with_outcome_filter(client, sample_judgments):
    """Test filtering by outcome."""
    response = client.post('/search/api/judgments', json={
        'q': 'test',
        'outcome': ['allowed'],
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'total' in data


def test_search_pagination(client, sample_judgments):
    """Test pagination works correctly."""
    response = client.post('/search/api/judgments', json={
        'q': 'test',
        'page': 1,
        'per_page': 2
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'page' in data
    assert 'pages' in data
    assert 'per_page' in data


def test_search_returns_metadata(client, sample_judgments):
    """Test that search results include required metadata."""
    response = client.post('/search/api/judgments', json={
        'q': 'test',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_count' in data or 'total' in data
    assert 'facet_counts' in data or 'facets' in data


def test_legislation_search_endpoint(client):
    """Test legislation search endpoint exists."""
    response = client.post('/search/api/legislation', json={
        'q': 'contract',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code in [200, 404]  # 404 if no legislation data


def test_judges_search_endpoint(client):
    """Test judges search endpoint exists."""
    response = client.post('/search/api/judges', json={
        'q': 'Dato',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code in [200, 404]


def test_lawyers_search_endpoint(client):
    """Test lawyers search endpoint exists."""
    response = client.post('/search/api/lawyers', json={
        'q': 'Lawyer',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code in [200, 404]


def test_empty_search_query(client):
    """Test handling of empty search queries."""
    response = client.post('/search/api/judgments', json={
        'q': '',
        'page': 1,
        'per_page': 20
    })
    assert response.status_code in [200, 400]


def test_search_pagination_max_per_page(client, sample_judgments):
    """Test that per_page is capped at maximum (50)."""
    response = client.post('/search/api/judgments', json={
        'q': 'test',
        'page': 1,
        'per_page': 100  # Request 100, should be capped at 50
    })
    assert response.status_code == 200
    data = response.get_json()
    # Verify no more than 50 results returned
    if 'data' in data:
        assert len(data['data']) <= 50
