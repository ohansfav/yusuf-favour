from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Department, Program, Course, AuditLog, StudentProfile
from utils.decorators import role_required
from utils.audit import log_action

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'users': User.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'lecturers': User.query.filter_by(role='lecturer').count(),
        'departments': Department.query.count(),
        'programs': Program.query.count(),
        'courses': Course.query.count(),
    }
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)


@admin_bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()
    return render_template('admin/manage_users.html', users=users, departments=departments)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'student')
    department_id = request.form.get('department_id')

    if not all([username, email, full_name, password]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if User.query.filter((User.username == username) | (User.email == email)).first():
        flash('Username or email already exists.', 'danger')
        return redirect(url_for('admin.manage_users'))

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        department_id=int(department_id) if department_id else None
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # If student role, create student profile
    if role == 'student':
        matric = request.form.get('matric_number', '').strip()
        program_id = request.form.get('program_id')
        level = request.form.get('level', 100)
        admission_year = request.form.get('admission_year', 2025)

        if matric and program_id:
            profile = StudentProfile(
                user_id=user.id,
                matric_number=matric,
                program_id=int(program_id),
                level=int(level),
                admission_year=int(admission_year)
            )
            db.session.add(profile)
            db.session.commit()

    log_action(current_user.id, 'CREATE', 'User', user.id,
               f'Created user {username} with role {role}')
    flash(f'User {username} created successfully.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.id != current_user.id:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        log_action(current_user.id, 'UPDATE', 'User', user.id,
                   f'User {user.username} {status}')
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/departments')
@login_required
@role_required('admin')
def manage_departments():
    departments = Department.query.all()
    programs = Program.query.all()
    return render_template('admin/manage_departments.html',
                           departments=departments, programs=programs)


@admin_bp.route('/departments/create', methods=['POST'])
@login_required
@role_required('admin')
def create_department():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()

    if not name or not code:
        flash('Department name and code are required.', 'danger')
        return redirect(url_for('admin.manage_departments'))

    if Department.query.filter((Department.name == name) | (Department.code == code)).first():
        flash('Department name or code already exists.', 'danger')
        return redirect(url_for('admin.manage_departments'))

    dept = Department(name=name, code=code)
    db.session.add(dept)
    db.session.commit()
    log_action(current_user.id, 'CREATE', 'Department', dept.id,
               f'Created department {name} ({code})')
    flash(f'Department {name} created.', 'success')
    return redirect(url_for('admin.manage_departments'))


@admin_bp.route('/programs/create', methods=['POST'])
@login_required
@role_required('admin')
def create_program():
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    department_id = request.form.get('department_id')
    duration = request.form.get('duration_years', 3)

    if not all([name, code, department_id]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.manage_departments'))

    prog = Program(
        name=name, code=code,
        department_id=int(department_id),
        duration_years=int(duration)
    )
    db.session.add(prog)
    db.session.commit()
    log_action(current_user.id, 'CREATE', 'Program', prog.id,
               f'Created program {name} ({code})')
    flash(f'Program {name} created.', 'success')
    return redirect(url_for('admin.manage_departments'))


@admin_bp.route('/courses')
@login_required
@role_required('admin')
def manage_courses():
    courses = Course.query.all()
    programs = Program.query.all()
    lecturers = User.query.filter_by(role='lecturer', is_active=True).all()
    return render_template('admin/manage_courses.html',
                           courses=courses, programs=programs, lecturers=lecturers)


@admin_bp.route('/courses/create', methods=['POST'])
@login_required
@role_required('admin')
def create_course():
    code = request.form.get('code', '').strip().upper()
    title = request.form.get('title', '').strip()
    credit_units = request.form.get('credit_units', 2)
    semester = request.form.get('semester', 'First')
    level = request.form.get('level', 100)
    program_id = request.form.get('program_id')
    lecturer_id = request.form.get('lecturer_id')

    if not all([code, title, program_id]):
        flash('Course code, title, and program are required.', 'danger')
        return redirect(url_for('admin.manage_courses'))

    course = Course(
        code=code, title=title,
        credit_units=int(credit_units),
        semester=semester, level=int(level),
        program_id=int(program_id),
        lecturer_id=int(lecturer_id) if lecturer_id else None
    )
    db.session.add(course)
    db.session.commit()
    log_action(current_user.id, 'CREATE', 'Course', course.id,
               f'Created course {code} - {title}')
    flash(f'Course {code} created.', 'success')
    return redirect(url_for('admin.manage_courses'))


@admin_bp.route('/audit-log')
@login_required
@role_required('admin')
def audit_log():
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/audit_log.html', logs=logs)
