import logging
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.legislation import Act, Section, SubLegislation, SubLegislationType
from app.models.judgment import Judgment, Citation, CitationRelationship
from app.services.search_service import SearchService
from sqlalchemy import func, or_, and_

bp = Blueprint('legislation', __name__, url_prefix='/legislation')
logger = logging.getLogger(__name__)
search_service = SearchService()


@bp.route('/')
def index():
    """Browse all Acts grouped by category."""
    try:
        # Get all categories
        categories = db.session.query(Act.category).distinct().order_by(Act.category).all()
        categories = [c[0] for c in categories if c[0]]

        # Get acts grouped by category
        acts_by_category = {}
        for category in categories:
            acts = Act.query.filter_by(category=category).order_by(Act.title).all()
            acts_by_category[category] = acts

        return render_template(
            'legislation/browse.html',
            categories=categories,
            acts_by_category=acts_by_category
        )
    except Exception as e:
        logger.error(f'Failed to load legislation index: {e}')
        return render_template('legislation/browse.html', categories=[], acts_by_category={}, error='Failed to load acts')


@bp.route('/<int:act_id>')
def view_act(act_id):
    """View a specific Act with all its sections."""
    try:
        act = Act.query.get_or_404(act_id)

        # Get all sections for this act
        sections = Section.query.filter_by(act_id=act_id).order_by(
            func.cast(
                func.regexp_replace(Section.section_number, r'[A-Z]', ''),
                db.Integer
            ),
            Section.section_number
        ).all()

        # Get related judgments citing this act
        related_judgments = db.session.query(Judgment).join(
            Citation, Citation.judgment_id == Judgment.id
        ).filter(
            Citation.statute_reference.ilike(f'%{act.title}%')
        ).limit(10).all()

        return render_template(
            'legislation/act.html',
            act=act,
            sections=sections,
            related_judgments=related_judgments
        )
    except Exception as e:
        logger.error(f'Failed to load act {act_id}: {e}')
        return render_template('legislation/act.html', error='Act not found')


@bp.route('/<int:act_id>/section/<section_id>')
def view_section(act_id, section_id):
    """View a specific section of an Act."""
    try:
        act = Act.query.get_or_404(act_id)
        section = Section.query.filter_by(act_id=act_id, section_number=section_id).first_or_404()

        # Get all sections for navigation
        sections = Section.query.filter_by(act_id=act_id).order_by(Section.section_number).all()

        # Get related judgments citing this section
        related_judgments = db.session.query(Judgment).join(
            Citation, Citation.judgment_id == Judgment.id
        ).filter(
            Citation.statute_reference.ilike(f'%Section {section_id}%'),
            Citation.statute_reference.ilike(f'%{act.title}%')
        ).limit(5).all()

        return render_template(
            'legislation/section.html',
            act=act,
            section=section,
            sections=sections,
            related_judgments=related_judgments
        )
    except Exception as e:
        logger.error(f'Failed to load section {section_id} of act {act_id}: {e}')
        return render_template('legislation/section.html', error='Section not found')


@bp.route('/search', methods=['POST'])
@login_required
def search():
    """Full-text and semantic search of legislation."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        page = int(data.get('page', 1))

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Search in Act titles and Section content
        results = db.session.query(Act).filter(
            or_(
                Act.title.ilike(f'%{query}%'),
                Act.summary.ilike(f'%{query}%')
            )
        ).order_by(Act.title).paginate(page=page, per_page=20)

        # Also search sections
        section_results = db.session.query(Section).filter(
            Section.content.ilike(f'%{query}%')
        ).limit(10).all()

        return jsonify({
            'acts': [
                {
                    'id': act.id,
                    'title': act.title,
                    'year': act.year,
                    'category': act.category,
                    'summary': act.summary[:200] if act.summary else ''
                }
                for act in results.items
            ],
            'sections': [
                {
                    'id': section.id,
                    'act_id': section.act_id,
                    'act_title': section.act.title,
                    'section_number': section.section_number,
                    'heading': section.heading,
                    'content': section.content[:200] if section.content else ''
                }
                for section in section_results
            ],
            'total': results.total,
            'page': page,
            'pages': results.pages
        })
    except Exception as e:
        logger.error(f'Legislation search failed: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/subsidiary')
def subsidiary_legislation():
    """Browse subsidiary legislation (PU(A) and PU(B))."""
    try:
        page = request.args.get('page', 1, type=int)
        pu_type = request.args.get('type', '', type=str)

        query = SubLegislation.query

        if pu_type in ['PU_A', 'PU_B']:
            query = query.filter_by(type=pu_type)

        results = query.order_by(SubLegislation.gazetted_date.desc()).paginate(
            page=page, per_page=50
        )

        return render_template(
            'legislation/subsidiary.html',
            sub_legislations=results.items,
            total=results.total,
            page=page,
            pages=results.pages,
            pu_type=pu_type
        )
    except Exception as e:
        logger.error(f'Failed to load subsidiary legislation: {e}')
        return render_template('legislation/subsidiary.html', error='Failed to load subsidiary legislation')
