import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.extensions import db
from app.models.user import User, Subscription, SubscriptionStatus
from app.models.analytics import AIUsage

logger = logging.getLogger(__name__)


class UsageService:
    """Manages AI query quotas, usage tracking, and cost calculation."""

    # Claude API pricing (as of 2024)
    PRICING = {
        'input_tokens': 0.003 / 1000,  # $0.003 per 1K input tokens
        'output_tokens': 0.015 / 1000,  # $0.015 per 1K output tokens
    }

    # Plan quotas (queries per month)
    PLAN_QUOTAS = {
        'free': 0,
        'research': 50,  # Research & Judge Analytics
        'professional': 500,  # Law Firms or Corporations
        'enterprise': 999999,
    }

    @staticmethod
    def get_current_plan(user):
        """
        Get user's active subscription plan.

        Args:
            user: User object

        Returns:
            tuple: (plan_name, Subscription object or None)
        """
        if not user or not user.subscriptions:
            return 'free', None

        active_sub = user.subscriptions.filter(
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIAL
            ])
        ).order_by(Subscription.created_at.desc()).first()

        if active_sub:
            return active_sub.plan, active_sub
        return 'free', None

    @staticmethod
    def get_monthly_quota(user):
        """
        Get user's monthly AI query quota based on plan.

        Args:
            user: User object

        Returns:
            int: Monthly quota limit
        """
        plan, _ = UsageService.get_current_plan(user)
        return UsageService.PLAN_QUOTAS.get(plan, 0)

    @staticmethod
    def get_current_month_usage(user):
        """
        Get current month's AI query usage count.

        Args:
            user: User object

        Returns:
            int: Number of queries used this month
        """
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        usage_count = db.session.query(func.count(AIUsage.id)).filter(
            and_(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= month_start
            )
        ).scalar() or 0

        return usage_count

    @staticmethod
    def get_monthly_cost(user):
        """
        Get current month's AI usage cost.

        Args:
            user: User object

        Returns:
            float: Total cost in USD
        """
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        total_cost = db.session.query(func.sum(AIUsage.cost_usd)).filter(
            and_(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= month_start
            )
        ).scalar() or 0.0

        return round(float(total_cost), 4)

    @staticmethod
    def can_use_ai_tool(user):
        """
        Check if user can use AI tools (has quota remaining).

        Args:
            user: User object

        Returns:
            tuple: (allowed: bool, reason: str)
        """
        if not user:
            return False, 'Not authenticated'

        plan, _ = UsageService.get_current_plan(user)
        quota = UsageService.get_monthly_quota(user)

        if quota == 0:
            return False, f'Plan "{plan}" does not include AI tools. Upgrade to access.'

        usage = UsageService.get_current_month_usage(user)

        if usage >= quota:
            return False, f'Monthly quota ({quota} queries) exceeded. Usage resets on the 1st of next month.'

        return True, ''

    @staticmethod
    def check_and_log_usage(user, tool_name, input_tokens, output_tokens):
        """
        Check quota and log AI usage if allowed.
        Raises exception if quota exceeded.

        Args:
            user: User object
            tool_name: Name of AI tool used (e.g., 'case-analyser')
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            AIUsage: Created usage record

        Raises:
            ValueError: If quota exceeded
        """
        allowed, reason = UsageService.can_use_ai_tool(user)
        if not allowed:
            raise ValueError(reason)

        # Calculate cost
        input_cost = input_tokens * UsageService.PRICING['input_tokens']
        output_cost = output_tokens * UsageService.PRICING['output_tokens']
        total_cost = input_cost + output_cost

        # Create usage record
        usage = AIUsage(
            user_id=user.id,
            tool_name=tool_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
            created_at=datetime.utcnow()
        )

        try:
            db.session.add(usage)
            db.session.commit()
            logger.info(
                f'Logged AI usage: user={user.id}, tool={tool_name}, '
                f'tokens={input_tokens + output_tokens}, cost=${total_cost:.4f}'
            )
            return usage
        except Exception as e:
            db.session.rollback()
            logger.error(f'Failed to log usage: {e}')
            raise

    @staticmethod
    def get_remaining_quota(user):
        """
        Get remaining AI queries for current month.

        Args:
            user: User object

        Returns:
            int: Remaining queries (0 if unlimited)
        """
        quota = UsageService.get_monthly_quota(user)
        if quota == 999999:  # Unlimited plan
            return -1

        usage = UsageService.get_current_month_usage(user)
        return max(0, quota - usage)

    @staticmethod
    def get_usage_stats(user):
        """
        Get comprehensive usage statistics for a user.

        Args:
            user: User object

        Returns:
            dict: Usage stats including quota, usage, cost, by-tool breakdown
        """
        plan, subscription = UsageService.get_current_plan(user)
        quota = UsageService.get_monthly_quota(user)
        usage = UsageService.get_current_month_usage(user)
        remaining = UsageService.get_remaining_quota(user)
        cost = UsageService.get_monthly_cost(user)

        # By-tool breakdown
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        tool_stats = db.session.query(
            AIUsage.tool_name,
            func.count(AIUsage.id).label('count'),
            func.sum(AIUsage.cost_usd).label('cost')
        ).filter(
            and_(
                AIUsage.user_id == user.id,
                AIUsage.created_at >= month_start
            )
        ).group_by(AIUsage.tool_name).all()

        tools = [
            {
                'name': t[0],
                'count': t[1],
                'cost': round(float(t[2] or 0), 4)
            }
            for t in tool_stats
        ]

        return {
            'plan': plan,
            'subscription_active': subscription is not None,
            'quota_limit': quota,
            'usage_count': usage,
            'remaining_queries': remaining,
            'is_unlimited': quota == 999999,
            'monthly_cost': cost,
            'resets_on': datetime(now.year, now.month + 1 if now.month < 12 else 1, 1),
            'by_tool': tools,
        }

    @staticmethod
    def get_all_users_monthly_summary():
        """
        Get summary of all users' monthly usage for admin dashboard.

        Returns:
            list: List of dicts with user usage summary
        """
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        users = User.query.filter_by(is_active=True).all()
        summary = []

        for user in users:
            plan, _ = UsageService.get_current_plan(user)
            quota = UsageService.get_monthly_quota(user)
            usage = UsageService.get_current_month_usage(user)
            cost = UsageService.get_monthly_cost(user)

            summary.append({
                'user_id': user.id,
                'email': user.email,
                'plan': plan,
                'quota': quota,
                'usage': usage,
                'cost': round(float(cost), 4),
                'percentage_used': round((usage / quota * 100) if quota > 0 else 0, 1),
            })

        return summary
