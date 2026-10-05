from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Result, ResultBatch, StudentProfile, Course, SemesterGPA
from utils.decorators import role_required
from utils.gpa import compute_cgpa

student_bp = Blueprint('student', __name__, template_folder='../templates/student')


@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    profile = current_user.student_profile
    if not profile:
        return render_template('student/dashboard.html', profile=None,
                               results=[], semester_gpas=[], cgpa=0, standing='N/A')

    # Only show published results
    results = (
        db.session.query(Result, Course, ResultBatch)
        .join(ResultBatch, Result.batch_id == ResultBatch.id)
        .join(Course, ResultBatch.course_id == Course.id)
        .filter(
            Result.student_id == profile.id,
            ResultBatch.status == 'REGISTRY_APPROVED'
        )
        .order_by(ResultBatch.academic_session.desc(), Course.level, Course.code)
        .all()
    )

    semester_gpas = SemesterGPA.query.filter_by(student_id=profile.id)\
        .order_by(SemesterGPA.academic_session, SemesterGPA.semester).all()

    cgpa, standing = compute_cgpa(profile.id)

    return render_template('student/dashboard.html',
                           profile=profile, results=results,
                           semester_gpas=semester_gpas,
                           cgpa=cgpa, standing=standing)


@student_bp.route('/results/<semester>/<session>')
@login_required
@role_required('student')
def semester_results(semester, session):
    profile = current_user.student_profile
    if not profile:
        return render_template('student/view_results.html', profile=None, results=[])

    results = (
        db.session.query(Result, Course, ResultBatch)
        .join(ResultBatch, Result.batch_id == ResultBatch.id)
        .join(Course, ResultBatch.course_id == Course.id)
        .filter(
            Result.student_id == profile.id,
            ResultBatch.semester == semester,
            ResultBatch.academic_session == session,
            ResultBatch.status == 'REGISTRY_APPROVED'
        )
        .order_by(Course.code)
        .all()
    )

    gpa_record = SemesterGPA.query.filter_by(
        student_id=profile.id, semester=semester, academic_session=session
    ).first()

    return render_template('student/view_results.html',
                           profile=profile, results=results,
                           semester=semester, session=session,
                           gpa_record=gpa_record)
