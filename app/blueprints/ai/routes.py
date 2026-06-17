from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.ai_tools_service import AIToolsService
from app.extensions import db
from datetime import datetime, timedelta

bp = Blueprint('ai', __name__, template_folder='templates')
ai_service = AIToolsService()


@bp.route('/', methods=['GET'])
@login_required
def dashboard():
    """AI Tools dashboard with all 6 tools."""
    # Check user plan
    user_plan = 'free'
    if current_user.subscriptions:
        active_sub = current_user.subscriptions.filter_by(
            status='active'
        ).first()
        if active_sub:
            user_plan = active_sub.plan

    # Calculate monthly quota usage (stub)
    queries_used = 0
    quota_limit = 0
    if user_plan == 'free':
        quota_limit = 0
    elif user_plan == 'starter':
        quota_limit = 50
    elif user_plan == 'professional':
        quota_limit = 500
    else:
        quota_limit = 999999

    tools = [
        {
            'id': 'case-analyser',
            'name': 'Case Analyser',
            'description': 'Analyze pleadings and assess case strength (1-10)',
            'icon': '⚖️',
            'locked': user_plan == 'free',
        },
        {
            'id': 'summariser',
            'name': 'Judgment Summariser',
            'description': 'Get structured summaries of judgments',
            'icon': '📄',
            'locked': user_plan == 'free',
        },
        {
            'id': 'argument-generator',
            'name': 'Legal Argument Generator',
            'description': 'Generate arguments backed by Malaysian case law',
            'icon': '💡',
            'locked': user_plan == 'free',
        },
        {
            'id': 'timeline-builder',
            'name': 'Case Timeline Builder',
            'description': 'Extract dates and visualize case chronology',
            'icon': '📅',
            'locked': user_plan == 'free',
        },
        {
            'id': 'counsel-research',
            'name': 'Opposing Counsel Research',
            'description': 'Get strategic intelligence on opposing counsel',
            'icon': '🔍',
            'locked': user_plan == 'free',
        },
        {
            'id': 'explain-law',
            'name': 'Legislation Explainer',
            'description': 'Plain-language explanations of statutes',
            'icon': '📚',
            'locked': user_plan == 'free',
        },
    ]

    return render_template(
        'ai/dashboard.html',
        tools=tools,
        queries_used=queries_used,
        quota_limit=quota_limit,
        user_plan=user_plan,
    )


@bp.route('/case-analyser', methods=['GET', 'POST'])
@login_required
def case_analyser():
    """Tool 1: Case Analyser"""
    if request.method == 'POST':
        pleading_text = request.form.get('pleading_text', '').strip()
        user_role = request.form.get('user_role', 'plaintiff')

        if not pleading_text:
            return jsonify({'error': 'Pleading text required'}), 400

        result = ai_service.analyze_case(pleading_text, user_role)
        return jsonify(result)

    return render_template('ai/case-analyser.html')


@bp.route('/summariser', methods=['GET', 'POST'])
@login_required
def summariser():
    """Tool 2: Judgment Summariser"""
    if request.method == 'POST':
        judgment_text = request.form.get('judgment_text', '').strip()
        language = request.form.get('language', 'en')

        if not judgment_text:
            return jsonify({'error': 'Judgment text required'}), 400

        result = ai_service.summarize_judgment(judgment_text, language)
        return jsonify(result)

    return render_template('ai/summariser.html')


@bp.route('/argument-generator', methods=['GET', 'POST'])
@login_required
def argument_generator():
    """Tool 3: Legal Argument Generator"""
    if request.method == 'POST':
        case_facts = request.form.get('case_facts', '').strip()
        user_role = request.form.get('user_role', 'plaintiff')
        subject_matter = request.form.get('subject_matter', 'Contract')

        if not case_facts:
            return jsonify({'error': 'Case facts required'}), 400

        result = ai_service.generate_legal_arguments(case_facts, user_role, subject_matter)
        return jsonify(result)

    return render_template('ai/argument-generator.html')


@bp.route('/timeline-builder', methods=['GET', 'POST'])
@login_required
def timeline_builder():
    """Tool 4: Case Timeline Builder"""
    if request.method == 'POST':
        documents = request.form.getlist('documents[]')
        documents = [d.strip() for d in documents if d.strip()]

        if not documents:
            return jsonify({'error': 'At least one document required'}), 400

        result = ai_service.build_case_timeline(documents)
        return jsonify(result)

    return render_template('ai/timeline-builder.html')


@bp.route('/counsel-research', methods=['GET', 'POST'])
@login_required
def counsel_research():
    """Tool 5: Opposing Counsel Research"""
    if request.method == 'POST':
        counsel_name = request.form.get('counsel_name', '').strip()

        if not counsel_name:
            return jsonify({'error': 'Counsel name required'}), 400

        result = ai_service.research_opposing_counsel(counsel_name)
        return jsonify(result)

    return render_template('ai/counsel-research.html')


@bp.route('/explain-law', methods=['GET', 'POST'])
@login_required
def explain_law():
    """Tool 6: Legislation Explainer"""
    if request.method == 'POST':
        section_text = request.form.get('section_text', '').strip()
        act_name = request.form.get('act_name', '').strip()
        language = request.form.get('language', 'en')

        if not section_text:
            return jsonify({'error': 'Section text required'}), 400

        result = ai_service.explain_legislation(section_text, act_name, language)
        return jsonify(result)

    return render_template('ai/explain-law.html')
