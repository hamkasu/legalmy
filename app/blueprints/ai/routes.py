from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.ai_tools_service import AIToolsService
from app.services.usage_service import UsageService
from app.decorators import require_ai_quota
from app.extensions import db
from datetime import datetime, timedelta

bp = Blueprint('ai', __name__, template_folder='templates')
ai_service = AIToolsService()


@bp.route('/', methods=['GET'])
@login_required
def dashboard():
    """AI Tools dashboard with all 6 tools and usage stats."""
    usage_stats = UsageService.get_usage_stats(current_user)
    user_plan = usage_stats['plan']
    quota_limit = usage_stats['quota_limit']
    queries_used = usage_stats['usage_count']
    remaining = usage_stats['remaining_queries']

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
        remaining_queries=remaining,
        is_unlimited=usage_stats['is_unlimited'],
        monthly_cost=usage_stats['monthly_cost'],
        by_tool=usage_stats['by_tool'],
        user_plan=user_plan,
    )


@bp.route('/case-analyser', methods=['GET', 'POST'])
@login_required
def case_analyser():
    """Tool 1: Case Analyser"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        pleading_text = request.form.get('pleading_text', '').strip()
        user_role = request.form.get('user_role', 'plaintiff')

        if not pleading_text:
            return jsonify({'error': 'Pleading text required'}), 400

        result = ai_service.analyze_case(pleading_text, user_role)

        if 'error' not in result:
            # Estimate token usage for logging (roughly 4 chars per token)
            input_tokens = len(pleading_text) // 4
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'case-analyser', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/case-analyser.html')


@bp.route('/summariser', methods=['GET', 'POST'])
@login_required
def summariser():
    """Tool 2: Judgment Summariser"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        judgment_text = request.form.get('judgment_text', '').strip()
        language = request.form.get('language', 'en')

        if not judgment_text:
            return jsonify({'error': 'Judgment text required'}), 400

        result = ai_service.summarize_judgment(judgment_text, language)

        if 'error' not in result:
            input_tokens = len(judgment_text) // 4
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'summariser', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/summariser.html')


@bp.route('/argument-generator', methods=['GET', 'POST'])
@login_required
def argument_generator():
    """Tool 3: Legal Argument Generator"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        case_facts = request.form.get('case_facts', '').strip()
        user_role = request.form.get('user_role', 'plaintiff')
        subject_matter = request.form.get('subject_matter', 'Contract')

        if not case_facts:
            return jsonify({'error': 'Case facts required'}), 400

        result = ai_service.generate_legal_arguments(case_facts, user_role, subject_matter)

        if 'error' not in result:
            input_tokens = len(case_facts) // 4
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'argument-generator', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/argument-generator.html')


@bp.route('/timeline-builder', methods=['GET', 'POST'])
@login_required
def timeline_builder():
    """Tool 4: Case Timeline Builder"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        documents = request.form.getlist('documents[]')
        documents = [d.strip() for d in documents if d.strip()]

        if not documents:
            return jsonify({'error': 'At least one document required'}), 400

        result = ai_service.build_case_timeline(documents)

        if 'error' not in result:
            input_tokens = sum(len(doc) // 4 for doc in documents)
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'timeline-builder', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/timeline-builder.html')


@bp.route('/counsel-research', methods=['GET', 'POST'])
@login_required
def counsel_research():
    """Tool 5: Opposing Counsel Research"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        counsel_name = request.form.get('counsel_name', '').strip()

        if not counsel_name:
            return jsonify({'error': 'Counsel name required'}), 400

        result = ai_service.research_opposing_counsel(counsel_name)

        if 'error' not in result:
            input_tokens = len(counsel_name) // 4 + 500
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'counsel-research', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/counsel-research.html')


@bp.route('/explain-law', methods=['GET', 'POST'])
@login_required
def explain_law():
    """Tool 6: Legislation Explainer"""
    if request.method == 'POST':
        allowed, reason = UsageService.can_use_ai_tool(current_user)
        if not allowed:
            return jsonify({
                'error': 'Quota exceeded or plan does not include AI tools',
                'message': reason,
            }), 402

        section_text = request.form.get('section_text', '').strip()
        act_name = request.form.get('act_name', '').strip()
        language = request.form.get('language', 'en')

        if not section_text:
            return jsonify({'error': 'Section text required'}), 400

        result = ai_service.explain_legislation(section_text, act_name, language)

        if 'error' not in result:
            input_tokens = (len(section_text) + len(act_name)) // 4
            output_tokens = len(str(result)) // 4
            try:
                UsageService.check_and_log_usage(
                    current_user, 'explain-law', input_tokens, output_tokens
                )
            except ValueError:
                pass

        return jsonify(result)

    return render_template('ai/explain-law.html')


@bp.route('/usage', methods=['GET'])
@login_required
def usage_stats():
    """Get usage statistics for API."""
    stats = UsageService.get_usage_stats(current_user)
    return jsonify(stats)
