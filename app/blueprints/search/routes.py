from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.search_service import SearchService
from app.models.judgment import CourtLevel, OutcomeType
from app.models.alert import SavedSearch
from app.extensions import db

bp = Blueprint('search', __name__, template_folder='templates')
search_service = SearchService()

# Malaysian states for location filter
MALAYSIAN_STATES = [
    'Johor', 'Kedah', 'Kelantan', 'Malacca', 'Negeri Sembilan',
    'Pahang', 'Penang', 'Perak', 'Perlis', 'Selangor', 'Terengganu',
    'Sabah', 'Sarawak', 'Federal Territories'
]


@bp.route('/', methods=['GET', 'POST'])
def index():
    """Search UI homepage."""
    return render_template(
        'search/index.html',
        states=MALAYSIAN_STATES,
        court_levels=[cl.value for cl in CourtLevel],
        outcomes=[ot.value for ot in OutcomeType],
    )


@bp.route('/api/judgments', methods=['POST'])
@login_required
def api_search_judgments():
    """
    Search judgments API endpoint.

    POST params:
        query: search string
        court_level: list of court levels
        court_location: list of states
        date_from, date_to: date range
        subject_matter: list of tags
        outcome: list of outcomes
        page: page number (default 1)
        per_page: results per page (default 20, max 100)
        semantic: enable semantic search (default true)

    Returns:
        JSON with results, total_count, page, pages, facets
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)
    semantic = data.get('semantic', True)

    # Build filters
    filters = {}
    if data.get('court_level'):
        filters['court_level'] = [
            CourtLevel[level] for level in data['court_level']
        ]
    if data.get('court_location'):
        filters['court_location'] = data['court_location']
    if data.get('date_from'):
        from datetime import datetime
        filters['date_from'] = datetime.fromisoformat(data['date_from']).date()
    if data.get('date_to'):
        from datetime import datetime
        filters['date_to'] = datetime.fromisoformat(data['date_to']).date()
    if data.get('subject_matter'):
        filters['subject_matter'] = data['subject_matter']
    if data.get('outcome'):
        filters['outcome'] = [
            OutcomeType[ot] for ot in data['outcome']
        ]
    if data.get('citation'):
        filters['citation'] = data['citation']
    if data.get('party_name'):
        filters['party_name'] = data['party_name']

    # Perform search
    results = search_service.search_judgments(
        query=query,
        filters=filters,
        page=page,
        per_page=per_page,
        semantic=semantic
    )

    # Serialize results
    serialized_results = [
        {
            'id': j.id,
            'citation': j.citation,
            'title': j.title,
            'court_level': j.court_level.value,
            'court_location': j.court_location,
            'date_decided': j.date_decided.isoformat() if j.date_decided else None,
            'subject_matter': j.subject_matter,
            'outcome': j.outcome.value if j.outcome else None,
            'summary': j.summary_ai or '',
        }
        for j in results['results']
    ]

    return jsonify({
        'status': 'success',
        'results': serialized_results,
        'total_count': results['total_count'],
        'page': results['page'],
        'pages': results['pages'],
        'facets': results['facets'],
    })


@bp.route('/api/legislation', methods=['POST'])
@login_required
def api_search_legislation():
    """Search legislation API endpoint."""
    data = request.get_json()
    query = data.get('query', '').strip()
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)

    results = search_service.search_legislation(
        query=query,
        filters=data.get('filters'),
        page=page,
        per_page=per_page
    )

    # Serialize results
    serialized = {}
    for act_id, act_data in results['results_by_act'].items():
        serialized[act_id] = {
            'act': {
                'id': act_data['act'].id,
                'short_title': act_data['act'].short_title,
                'act_number': act_data['act'].act_number,
            },
            'sections': [
                {
                    'id': s.id,
                    'section_number': s.section_number,
                    'heading': s.heading,
                    'content': s.content[:200],
                }
                for s in act_data['sections']
            ]
        }

    return jsonify({
        'status': 'success',
        'results_by_act': serialized,
        'total_count': results['total_count'],
        'page': results['page'],
        'pages': results['pages'],
    })


@bp.route('/api/judges', methods=['POST'])
@login_required
def api_search_judges():
    """Search judges API endpoint."""
    data = request.get_json()
    query = data.get('query', '').strip()
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)

    results = search_service.search_judges(
        query=query,
        filters=data.get('filters'),
        page=page,
        per_page=per_page
    )

    serialized_results = [
        {
            'id': j.id,
            'full_name': j.full_name,
            'title': j.title,
            'court_level': j.court_level.value,
            'court_location': j.court_location,
            'is_active': j.is_active,
        }
        for j in results['results']
    ]

    return jsonify({
        'status': 'success',
        'results': serialized_results,
        'total_count': results['total_count'],
        'page': results['page'],
        'pages': results['pages'],
    })


@bp.route('/api/lawyers', methods=['POST'])
@login_required
def api_search_lawyers():
    """Search lawyers API endpoint."""
    data = request.get_json()
    query = data.get('query', '').strip()
    page = data.get('page', 1)
    per_page = data.get('per_page', 20)

    results = search_service.search_lawyers(
        query=query,
        filters=data.get('filters'),
        page=page,
        per_page=per_page
    )

    serialized_results = [
        {
            'id': l.id,
            'full_name': l.full_name,
            'bar_council_number': l.bar_council_number,
            'firm_id': l.firm_id,
            'specialisations': l.specialisations,
            'is_active': l.is_active,
        }
        for l in results['results']
    ]

    return jsonify({
        'status': 'success',
        'results': serialized_results,
        'total_count': results['total_count'],
        'page': results['page'],
        'pages': results['pages'],
    })


@bp.route('/api/save-search', methods=['POST'])
@login_required
def api_save_search():
    """Save a search for later alerts."""
    data = request.get_json()
    name = data.get('name', '').strip()
    query_json = data.get('query_json', {})

    if not name:
        return jsonify({'status': 'error', 'message': 'Search name required'}), 400

    saved_search = SavedSearch(
        user_id=current_user.id,
        name=name,
        query_json=query_json
    )
    db.session.add(saved_search)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'saved_search_id': saved_search.id,
        'message': f'Search "{name}" saved successfully'
    })
