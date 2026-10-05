from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from utils.audit import log_action

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(_get_dashboard_route(current_user.role)))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(_get_dashboard_route(current_user.role)))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            log_action(None, 'LOGIN_FAILED', 'User', None,
                       f'Failed login attempt for username: {username}')
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Contact the administrator.', 'danger')
            return render_template('login.html')

        login_user(user, remember=False)
        log_action(user.id, 'LOGIN', 'User', user.id, f'User {user.username} logged in')

        next_page = request.args.get('next')
        # Prevent open redirect
        if next_page and not next_page.startswith('/'):
            next_page = None

        return redirect(next_page or url_for(_get_dashboard_route(user.role)))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'LOGOUT', 'User', current_user.id,
               f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _get_dashboard_route(role):
    routes = {
        'admin': 'admin.dashboard',
        'lecturer': 'lecturer.dashboard',
        'hod': 'hod.dashboard',
        'exam_officer': 'hod.dashboard',
        'registry': 'registry.dashboard',
        'student': 'student.dashboard',
    }
    return routes.get(role, 'auth.login')
