import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from app.extensions import db, mail
from app.models.user import User, Subscription, SubscriptionStatus
from app.decorators import require_plan
from datetime import datetime, timedelta
from flask_mail import Message
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)


def generate_verification_token(email):
    """Generate email verification token (24hr TTL)."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verify')


def verify_token(token, max_age=86400):
    """Verify email token with 24hr TTL."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verify', max_age=max_age)
        return email
    except Exception:
        return None


def send_verification_email(user):
    """Send email verification link."""
    try:
        token = generate_verification_token(user.email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        subject = 'Verify your LegalMY account'
        body = f"""Welcome to LegalMY!

Please verify your email address to activate your account:

{verify_url}

This link expires in 24 hours.

If you didn't create this account, please ignore this email.

— LegalMY Team"""
        msg = Message(subject, recipients=[user.email], body=body)
        mail.send(msg)
        logger.info(f'Verification email sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send verification email: {e}')
        return False


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        bar_council_number = request.form.get('bar_council_number', '').strip() or None

        # Validation
        if not all([email, full_name, password]):
            flash('Email, name, and password are required', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return render_template('auth/register.html')

        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')

        try:
            # Create user
            user = User(
                email=email,
                full_name=full_name,
                is_active=True,
                is_verified=False,
                bar_council_number=bar_council_number,
                is_lawyer=bool(bar_council_number)
            )
            user.set_password(password)

            # Create free subscription
            subscription = Subscription(
                user=user,
                plan='free',
                status=SubscriptionStatus.ACTIVE,
                started_at=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=365)
            )

            db.session.add(user)
            db.session.add(subscription)
            db.session.commit()

            # Send verification email
            if send_verification_email(user):
                flash('Registration successful! Check your email to verify your account.', 'success')
            else:
                flash('Registration successful! Please check spam folder for verification email.', 'warning')

            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Registration error: {e}')
            flash('Registration failed. Please try again.', 'danger')

    return render_template('auth/register.html')


@bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify email address."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    email = verify_token(token)
    if not email:
        flash('Verification link is invalid or expired', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'))

    if user.is_verified:
        flash('Email already verified', 'info')
        return redirect(url_for('auth.login'))

    try:
        user.is_verified = True
        db.session.commit()
        flash('Email verified successfully! You can now log in.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Email verification error: {e}')
        flash('Verification failed. Please try again.', 'danger')

    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not email or not password:
            flash('Email and password required', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Account is inactive', 'danger')
            return render_template('auth/login.html')

        if not user.is_verified:
            flash('Please verify your email before logging in', 'info')
            return render_template('auth/login.html')

        try:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            logger.info(f'User {email} logged in')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f'Login error: {e}')
            flash('Login failed. Please try again.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logger.info(f'User {current_user.email} logged out')
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('landing.index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            try:
                token = generate_verification_token(user.email)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                subject = 'Reset your LegalMY password'
                body = f"""Password Reset Request

Click the link below to reset your password:

{reset_url}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

— LegalMY Team"""
                msg = Message(subject, recipients=[user.email], body=body)
                mail.send(msg)
                logger.info(f'Password reset email sent to {user.email}')
            except Exception as e:
                logger.error(f'Failed to send password reset email: {e}')

        # Always show success for security
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    email = verify_token(token)
    if not email:
        flash('Password reset link is invalid or expired', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('auth/reset_password.html', token=token)

        try:
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(password)
                db.session.commit()
                flash('Password reset successfully! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Password reset error: {e}')
            flash('Password reset failed. Please try again.', 'danger')

    return render_template('auth/reset_password.html', token=token)


@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    subscription = current_user.subscription
    return render_template('auth/profile.html', subscription=subscription)


@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        full_name = request.form.get('full_name', '').strip()

        if not full_name:
            flash('Name is required', 'danger')
            return redirect(url_for('auth.profile'))

        current_user.full_name = full_name
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    except Exception as e:
        logger.error(f'Profile update error: {e}')
        flash('Profile update failed', 'danger')
        return redirect(url_for('auth.profile'))


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.profile'))

        if len(new_password) < 8:
            flash('New password must be at least 8 characters', 'danger')
            return redirect(url_for('auth.profile'))

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.profile'))

        current_user.set_password(new_password)
        db.session.commit()

        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.profile'))
    except Exception as e:
        logger.error(f'Password change error: {e}')
        flash('Password change failed', 'danger')
        return redirect(url_for('auth.profile'))


@bp.route('/upgrade/<plan>')
@login_required
def upgrade_plan(plan):
    """Redirect to Stripe Checkout."""
    from app.services.stripe_service import StripeService

    valid_plans = ['starter', 'professional', 'firm']
    if plan not in valid_plans:
        flash('Invalid plan', 'danger')
        return redirect(url_for('pricing.index'))

    try:
        stripe_service = StripeService()
        checkout_url = stripe_service.create_checkout_session(current_user.id, plan)
        return redirect(checkout_url)
    except Exception as e:
        logger.error(f'Stripe checkout error: {e}')
        flash('Unable to process upgrade. Please try again.', 'danger')
        return redirect(url_for('pricing.index'))
