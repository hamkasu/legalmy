from functools import wraps
from flask import jsonify, redirect, url_for, flash, request
from flask_login import current_user
from app.config import PLANS


def require_plan(min_plan):
    """
    Decorator to require minimum subscription plan.
    Usage: @require_plan('starter')

    Returns 402 JSON for API routes, redirects to /pricing for web routes.
    """
    plan_hierarchy = {
        'free': 0,
        'starter': 1,
        'professional': 2,
        'firm': 3,
    }

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request_wants_json():
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login', next=request.url))

            user_plan = current_user.subscription.plan if current_user.subscription else 'free'
            user_level = plan_hierarchy.get(user_plan, 0)
            required_level = plan_hierarchy.get(min_plan, 0)

            if user_level < required_level:
                if request_wants_json():
                    return jsonify({
                        'error': 'Upgrade required',
                        'message': f'This feature requires {PLANS[min_plan]["name"]} plan or above',
                        'upgrade_url': url_for('pricing.index', _external=True)
                    }), 402

                flash(f'This feature requires {PLANS[min_plan]["name"]} plan or above', 'warning')
                return redirect(url_for('pricing.index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def request_wants_json():
    """Check if request prefers JSON response."""
    return request.path.startswith('/api/') or \
           request.accept_mimetypes.get('application/json', 0) > \
           request.accept_mimetypes.get('text/html', 0)
