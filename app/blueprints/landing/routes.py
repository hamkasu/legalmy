from flask import Blueprint, render_template

bp = Blueprint('landing', __name__)


@bp.route('/')
def index():
    """Landing page / homepage."""
    return render_template('landing/index.html')


@bp.route('/about')
def about():
    """About page / company story."""
    return render_template('landing/about.html')


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page."""
    from flask import request, flash, redirect, url_for

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, message]):
            flash('All fields are required', 'danger')
            return redirect(url_for('landing.contact'))

        # Would send email here
        flash('Thank you for your message. We will get back to you soon!', 'success')
        return redirect(url_for('landing.contact'))

    return render_template('landing/contact.html')
