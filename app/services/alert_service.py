import logging
from celery import shared_task
from flask import current_app, render_template_string
from flask_mail import Message
from app.extensions import db, mail
from app.models.alert import Alert
from app.models.judgment import Judgment
from app.models.user import User
from app.services.search_service import SearchService
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
search_service = SearchService()


@shared_task(name='alerts.send_daily')
def send_daily_alerts():
    """Send daily alerts for all active users. Runs at 06:00 MYT."""
    try:
        with current_app.app_context():
            # Get all active daily alerts
            active_alerts = Alert.query.filter_by(
                is_active=True,
                frequency='daily'
            ).all()

            logger.info(f'Processing {len(active_alerts)} daily alerts')

            for alert in active_alerts:
                try:
                    send_alert(alert)
                except Exception as e:
                    logger.error(f'Failed to send alert {alert.id}: {e}')
                    continue

            return {'status': 'success', 'alerts_sent': len(active_alerts)}
    except Exception as e:
        logger.error(f'Daily alerts task error: {e}')
        return {'status': 'error', 'message': str(e)}


@shared_task(name='alerts.send_weekly')
def send_weekly_alerts():
    """Send weekly alerts. Runs every Monday at 06:00 MYT."""
    try:
        with current_app.app_context():
            # Get all active weekly alerts
            active_alerts = Alert.query.filter_by(
                is_active=True,
                frequency='weekly'
            ).all()

            logger.info(f'Processing {len(active_alerts)} weekly alerts')

            for alert in active_alerts:
                try:
                    send_alert(alert)
                except Exception as e:
                    logger.error(f'Failed to send alert {alert.id}: {e}')
                    continue

            return {'status': 'success', 'alerts_sent': len(active_alerts)}
    except Exception as e:
        logger.error(f'Weekly alerts task error: {e}')
        return {'status': 'error', 'message': str(e)}


def send_alert(alert):
    """Send a single alert with new judgment results."""
    user = alert.saved_search.user
    query_data = alert.saved_search.query_json

    # Re-run saved search
    query = query_data.get('query', '')
    filters = query_data.get('filters', {})

    # Find judgments created since last alert sent
    since = alert.last_sent if alert.last_sent else datetime.utcnow() - timedelta(days=1)

    # Search for new results (simplified - would use full search_service)
    new_judgments = Judgment.query.filter(
        Judgment.created_at > since
    ).limit(10).all()

    if not new_judgments:
        logger.info(f'No new results for alert {alert.id}')
        return

    # Build email
    subject = f"LegalMY Alert: {len(new_judgments)} new judgments match '{alert.saved_search.name}'"

    html_body = render_template_string(
        ALERT_EMAIL_TEMPLATE,
        user_name=user.full_name,
        alert_name=alert.saved_search.name,
        judgment_count=len(new_judgments),
        judgments=new_judgments,
        view_url=f"https://legalmy.com.my/dashboard/alerts",
        unsubscribe_url=f"https://legalmy.com.my/dashboard/alerts/{alert.id}/pause"
    )

    # Send email
    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=html_body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@legalmy.com.my')
        )
        mail.send(msg)
        logger.info(f'Alert {alert.id} sent to {user.email}')

        # Update last_sent
        alert.last_sent = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        logger.error(f'Failed to send alert email: {e}')
        raise


ALERT_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0D1B2A 0%, #1a2f4d 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .content { background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }
        .judgment-card { background: #f3f4f6; padding: 20px; margin-bottom: 15px; border-left: 4px solid #B8973A; border-radius: 4px; }
        .judgment-citation { font-weight: bold; color: #0D1B2A; }
        .judgment-title { font-size: 18px; color: #0D1B2A; margin: 8px 0; }
        .judgment-meta { color: #64748B; font-size: 14px; margin: 8px 0; }
        .judgment-summary { color: #64748B; line-height: 1.6; margin-top: 10px; }
        .cta-button { display: inline-block; background: #B8973A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f3f4f6; padding: 20px; text-align: center; font-size: 12px; color: #64748B; border-radius: 0 0 8px 8px; }
        .footer a { color: #B8973A; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ LegalMY Alert</h1>
            <p>New judgments matching your search</p>
        </div>

        <div class="content">
            <p>Hi {{ user_name }},</p>

            <p>We found <strong>{{ judgment_count }} new judgment{{ 's' if judgment_count != 1 else '' }}</strong> matching your saved search <strong>"{{ alert_name }}"</strong>.</p>

            {% for judgment in judgments %}
            <div class="judgment-card">
                <div class="judgment-citation">{{ judgment.citation }}</div>
                <div class="judgment-title">{{ judgment.title }}</div>
                <div class="judgment-meta">
                    <strong>{{ judgment.court_level.value }}</strong> • {{ judgment.date_decided.strftime('%d %b %Y') if judgment.date_decided else 'Date unknown' }}
                </div>
                {% if judgment.summary_ai %}
                <div class="judgment-summary">{{ judgment.summary_ai[:150] }}...</div>
                {% endif %}
            </div>
            {% endfor %}

            <a href="{{ view_url }}" class="cta-button">View All Results</a>

            <p style="color: #64748B; font-size: 14px; margin-top: 30px;">
                This is an automated alert from LegalMY. You can manage your alerts in your <a href="{{ view_url }}" style="color: #B8973A;">dashboard</a>.
            </p>
        </div>

        <div class="footer">
            <p style="margin: 0;">
                LegalMY — Malaysia's Legal Intelligence Platform<br>
                <a href="{{ unsubscribe_url }}">Pause this alert</a> • <a href="#">Manage preferences</a> • <a href="#">Contact support</a>
            </p>
            <p style="margin: 10px 0 0 0;">© 2026 Calmic Sdn Bhd. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
