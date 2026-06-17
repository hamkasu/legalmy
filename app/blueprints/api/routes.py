import logging
import uuid
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import ApiKey, User
from app.models.judgment import Judgment, Citation, CitationRelationship
from app.models.judge import Judge, JudgeAnalytics
from app.models.legislation import Act, Section
from app.services.api_key_service import ApiKeyService
from sqlalchemy import or_, and_

bp = Blueprint('api', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)


def api_response(status, data=None, error=None, meta=None):
    """Standard API response wrapper."""
    response = {'status': status}

    if data is not None:
        response['data'] = data

    if error is not None:
        response['error'] = error

    response['meta'] = meta or {
        'api_version': '1.0',
        'request_id': str(uuid.uuid4()),
    }

    return response


def require_api_key(f):
    """Decorator to verify API key from Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify(api_response('error', error={
                'code': 'MISSING_API_KEY',
                'message': 'Authorization header required. Format: Bearer <api_key>'
            })), 401

        api_key_string = auth_header[7:]
        api_key = ApiKeyService.verify_api_key(api_key_string)

        if not api_key:
            return jsonify(api_response('error', error={
                'code': 'INVALID_API_KEY',
                'message': 'Invalid or revoked API key'
            })), 401

        # Check subscription
        user = api_key.user
        subscription = user.subscriptions.first() if user else None
        if not user or not subscription or subscription.plan != 'firm':
            return jsonify(api_response('error', error={
                'code': 'SUBSCRIPTION_REQUIRED',
                'message': 'API access requires Firm plan subscription',
                'upgrade_url': 'https://legalmy.com.my/pricing'
            })), 402

        # Check rate limit
        usage_today = ApiKeyService.get_usage_today(user.id)
        limit = ApiKeyService.get_usage_limit(user.id)

        if usage_today >= limit:
            return jsonify(api_response('error', error={
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': f'You have exceeded your daily API quota of {limit} requests',
                'upgrade_url': 'https://legalmy.com.my/pricing'
            })), 429

        # Pass user and usage info to route
        request.api_user = user
        request.api_usage = usage_today
        request.api_limit = limit

        return f(*args, **kwargs)

    return decorated_function


# ===== JUDGMENTS =====

@bp.route('/judgments', methods=['GET'])
@require_api_key
def list_judgments():
    """List judgments with filters and pagination."""
    try:
        court_level = request.args.get('court_level')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        subject_matter = request.args.get('subject_matter', '').split(',') if request.args.get('subject_matter') else []
        outcome = request.args.get('outcome')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        query = Judgment.query

        if court_level:
            query = query.filter_by(court_level=court_level)

        if date_from:
            query = query.filter(Judgment.date_decided >= datetime.fromisoformat(date_from))

        if date_to:
            query = query.filter(Judgment.date_decided <= datetime.fromisoformat(date_to))

        if outcome:
            query = query.filter_by(outcome=outcome)

        results = query.paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': j.id,
                    'citation': j.citation,
                    'title': j.title,
                    'court_level': j.court_level.value if hasattr(j.court_level, 'value') else j.court_level,
                    'court_location': j.court_location,
                    'date_decided': j.date_decided.isoformat() if j.date_decided else None,
                    'outcome': j.outcome,
                    'summary': j.summary_ai[:200] if j.summary_ai else None,
                }
                for j in results.items
            ],
            'total': results.total,
            'page': page,
            'pages': results.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'List judgments error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/judgments/<uuid:judgment_id>', methods=['GET'])
@require_api_key
def get_judgment(judgment_id):
    """Get full judgment detail with citation graph."""
    try:
        judgment = Judgment.query.get_or_404(judgment_id)

        # Citation graph (edges in/out)
        citing = Citation.query.filter_by(cited_judgment_id=judgment_id).all()
        cited_by = Citation.query.filter_by(citing_judgment_id=judgment_id).all()

        data = {
            'id': str(judgment.id),
            'citation': judgment.citation,
            'title': judgment.title,
            'court_level': judgment.court_level.value if hasattr(judgment.court_level, 'value') else judgment.court_level,
            'court_location': judgment.court_location,
            'date_decided': judgment.date_decided.isoformat() if judgment.date_decided else None,
            'full_text': judgment.full_text,
            'summary': judgment.summary_ai,
            'outcome': judgment.outcome,
            'coram': judgment.coram if judgment.coram else [],
            'parties_plaintiff': judgment.parties_plaintiff if judgment.parties_plaintiff else [],
            'parties_defendant': judgment.parties_defendant if judgment.parties_defendant else [],
            'subject_matter': judgment.subject_matter if judgment.subject_matter else [],
            'citation_graph': {
                'citing': [
                    {
                        'judgment_id': str(c.citing_judgment_id),
                        'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship
                    }
                    for c in citing
                ],
                'cited_by': [
                    {
                        'judgment_id': str(c.cited_judgment_id),
                        'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship
                    }
                    for c in cited_by
                ]
            }
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get judgment error: {e}')
        return jsonify(api_response('error', error={
            'code': 'NOT_FOUND',
            'message': 'Judgment not found'
        })), 404


@bp.route('/judgments/search', methods=['GET'])
@require_api_key
def search_judgments():
    """Hybrid search: full-text + semantic (placeholder)."""
    try:
        query = request.args.get('q', '').strip()
        semantic = request.args.get('semantic', 'true').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        if not query:
            return jsonify(api_response('error', error={
                'code': 'MISSING_QUERY',
                'message': 'q parameter required'
            })), 400

        # Simple full-text search
        results = Judgment.query.filter(
            or_(
                Judgment.title.ilike(f'%{query}%'),
                Judgment.full_text.ilike(f'%{query}%')
            )
        ).paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': j.id,
                    'citation': j.citation,
                    'title': j.title,
                    'court_level': j.court_level.value if hasattr(j.court_level, 'value') else j.court_level,
                    'date_decided': j.date_decided.isoformat() if j.date_decided else None,
                    'score': 0.95,  # Placeholder
                    'summary': j.summary_ai[:200] if j.summary_ai else None,
                }
                for j in results.items
            ],
            'total': results.total,
            'page': page,
            'pages': results.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Search judgments error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


# ===== JUDGES =====

@bp.route('/judges', methods=['GET'])
@require_api_key
def list_judges():
    """List judges with basic info."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        judges = Judge.query.paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': j.id,
                    'full_name': j.full_name,
                    'court_level': j.court_level.value if hasattr(j.court_level, 'value') else j.court_level,
                    'court_location': j.court_location,
                    'is_active': j.is_active,
                }
                for j in judges.items
            ],
            'total': judges.total,
            'page': page,
            'pages': judges.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'List judges error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/judges/<int:judge_id>', methods=['GET'])
@require_api_key
def get_judge(judge_id):
    """Get judge profile with analytics."""
    try:
        judge = Judge.query.get_or_404(judge_id)
        analytics = JudgeAnalytics.query.filter_by(judge_id=judge_id).first()

        data = {
            'id': judge.id,
            'full_name': judge.full_name,
            'court_level': judge.court_level.value if hasattr(judge.court_level, 'value') else judge.court_level,
            'court_location': judge.court_location,
            'date_appointed': judge.date_appointed.isoformat() if judge.date_appointed else None,
            'date_retired': judge.date_retired.isoformat() if judge.date_retired else None,
            'is_active': judge.is_active,
            'analytics': {
                'total_cases': analytics.total_cases if analytics else 0,
                'plaintiff_win_rate': analytics.plaintiff_win_rate if analytics else None,
                'defendant_win_rate': analytics.defendant_win_rate if analytics else None,
                'avg_days_to_judgment': analytics.avg_days_to_judgment if analytics else None,
            } if analytics else None
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get judge error: {e}')
        return jsonify(api_response('error', error={
            'code': 'NOT_FOUND',
            'message': 'Judge not found'
        })), 404


@bp.route('/judges/<int:judge_id>/judgments', methods=['GET'])
@require_api_key
def get_judge_judgments(judge_id):
    """Get judgments by a specific judge."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        # Would filter by judge in coram array
        judgments = Judgment.query.limit(50).paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': j.id,
                    'citation': j.citation,
                    'title': j.title,
                    'date_decided': j.date_decided.isoformat() if j.date_decided else None,
                }
                for j in judgments.items
            ],
            'total': judgments.total,
            'page': page,
            'pages': judgments.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get judge judgments error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


# ===== LEGISLATION =====

@bp.route('/acts', methods=['GET'])
@require_api_key
def list_acts():
    """List all Acts."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        acts = Act.query.paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': a.id,
                    'title': a.title,
                    'year': a.year,
                    'category': a.category,
                }
                for a in acts.items
            ],
            'total': acts.total,
            'page': page,
            'pages': acts.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'List acts error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/acts/<int:act_id>/sections', methods=['GET'])
@require_api_key
def get_act_sections(act_id):
    """Get all sections of an Act."""
    try:
        sections = Section.query.filter_by(act_id=act_id).all()

        data = {
            'data': [
                {
                    'id': s.id,
                    'section_number': s.section_number,
                    'heading': s.heading,
                    'content': s.content[:500] if s.content else None,
                }
                for s in sections
            ],
            'total': len(sections)
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get act sections error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/legislation/search', methods=['GET'])
@require_api_key
def search_legislation():
    """Search legislation by keyword."""
    try:
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        if not query:
            return jsonify(api_response('error', error={
                'code': 'MISSING_QUERY',
                'message': 'q parameter required'
            })), 400

        sections = Section.query.filter(
            Section.content.ilike(f'%{query}%')
        ).paginate(page=page, per_page=per_page)

        data = {
            'data': [
                {
                    'id': s.id,
                    'act_id': s.act_id,
                    'section_number': s.section_number,
                    'heading': s.heading,
                    'content': s.content[:200] if s.content else None,
                }
                for s in sections.items
            ],
            'total': sections.total,
            'page': page,
            'pages': sections.pages
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Search legislation error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


# ===== CITATION GRAPH =====

@bp.route('/citations/<uuid:judgment_id>/citing', methods=['GET'])
@require_api_key
def get_citing_cases(judgment_id):
    """Get cases that cite this judgment."""
    try:
        citing = Citation.query.filter_by(cited_judgment_id=judgment_id).all()

        data = {
            'data': [
                {
                    'judgment_id': str(c.citing_judgment_id),
                    'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship,
                }
                for c in citing
            ],
            'total': len(citing)
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get citing cases error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/citations/<uuid:judgment_id>/cited', methods=['GET'])
@require_api_key
def get_cited_cases(judgment_id):
    """Get cases cited by this judgment."""
    try:
        cited = Citation.query.filter_by(citing_judgment_id=judgment_id).all()

        data = {
            'data': [
                {
                    'judgment_id': str(c.cited_judgment_id),
                    'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship,
                }
                for c in cited
            ],
            'total': len(cited)
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get cited cases error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500


@bp.route('/citations/<uuid:judgment_id>/graph', methods=['GET'])
@require_api_key
def get_citation_graph(judgment_id):
    """Get full citation network for graph rendering."""
    try:
        depth = request.args.get('depth', 1, type=int)
        depth = min(depth, 3)  # Max depth 3

        # Build node and edge lists
        nodes = []
        edges = []

        # Add focal node
        focal = Judgment.query.get(judgment_id)
        if focal:
            nodes.append({
                'id': str(focal.id),
                'label': focal.citation,
                'year': focal.date_decided.year if focal.date_decided else None,
                'court': focal.court_level.value if hasattr(focal.court_level, 'value') else focal.court_level,
                'outcome': focal.outcome,
            })

        # Add citing cases
        citing = Citation.query.filter_by(cited_judgment_id=judgment_id).all()
        for c in citing[:20]:
            edges.append({
                'source': str(c.citing_judgment_id),
                'target': str(judgment_id),
                'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship,
            })

        # Add cited cases
        cited = Citation.query.filter_by(citing_judgment_id=judgment_id).all()
        for c in cited[:20]:
            edges.append({
                'source': str(judgment_id),
                'target': str(c.cited_judgment_id),
                'relationship': c.relationship.value if hasattr(c.relationship, 'value') else c.relationship,
            })

        data = {
            'nodes': nodes,
            'edges': edges
        }

        meta = {
            'api_version': '1.0',
            'request_id': str(uuid.uuid4()),
            'usage': {
                'requests_today': request.api_usage + 1,
                'requests_limit': request.api_limit
            }
        }

        return jsonify(api_response('success', data=data, meta=meta)), 200
    except Exception as e:
        logger.error(f'Get citation graph error: {e}')
        return jsonify(api_response('error', error={
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        })), 500



# ===== DOCUMENTATION =====

@bp.route('/docs', methods=['GET'])
def api_docs():
    """API documentation page."""
    from flask import render_template
    return render_template('api_docs.html'), 200


@bp.route('/v1/openapi.json', methods=['GET'])
def openapi_schema():
    """OpenAPI 3.0 schema for API documentation."""
    schema = {
        'openapi': '3.0.0',
        'info': {
            'title': 'LegalMY API',
            'version': '1.0.0',
            'description': 'RESTful API for Malaysian legal research and analytics'
        },
        'servers': [
            {'url': 'https://legalmy.com.my/api/v1', 'description': 'Production'}
        ],
        'components': {
            'securitySchemes': {
                'bearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT'
                }
            }
        },
        'paths': {
            '/judgments': {
                'get': {
                    'summary': 'List judgments',
                    'parameters': [
                        {'name': 'page', 'in': 'query', 'schema': {'type': 'integer'}},
                        {'name': 'per_page', 'in': 'query', 'schema': {'type': 'integer', 'maximum': 50}}
                    ]
                }
            },
            '/judges': {
                'get': {
                    'summary': 'List judges'
                }
            },
            '/acts': {
                'get': {
                    'summary': 'List Acts'
                }
            }
        }
    }
    return jsonify(schema), 200
