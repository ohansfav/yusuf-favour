from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Course, ResultBatch, Result, StudentProfile
from utils.decorators import role_required
from utils.audit import log_action
from utils.gpa import compute_result

lecturer_bp = Blueprint('lecturer', __name__, template_folder='../templates/lecturer')


@lecturer_bp.route('/dashboard')
@login_required
@role_required('lecturer')
def dashboard():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    batches = ResultBatch.query.filter_by(lecturer_id=current_user.id)\
        .order_by(ResultBatch.created_at.desc()).all()
    return render_template('lecturer/dashboard.html', courses=courses, batches=batches)


@lecturer_bp.route('/upload/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required('lecturer')
def upload_marks(course_id):
    course = db.session.get(Course, course_id)
    if not course or course.lecturer_id != current_user.id:
        flash('Course not found or not assigned to you.', 'danger')
        return redirect(url_for('lecturer.dashboard'))

    # Get students enrolled in this course's program and level
    students = StudentProfile.query.filter_by(
        program_id=course.program_id,
        level=course.level
    ).all()

    if request.method == 'POST':
        semester = request.form.get('semester', 'First')
        academic_session = request.form.get('academic_session', '').strip()

        if not academic_session:
            flash('Academic session is required.', 'danger')
            return render_template('lecturer/upload_marks.html',
                                   course=course, students=students)

        # Check for existing draft batch
        existing = ResultBatch.query.filter_by(
            course_id=course_id,
            semester=semester,
            academic_session=academic_session,
            lecturer_id=current_user.id
        ).first()

        if existing and existing.status not in ('DRAFT', 'REJECTED'):
            flash('Results for this course/session have already been submitted.', 'warning')
            return redirect(url_for('lecturer.dashboard'))

        # Create or reuse batch
        if existing:
            batch = existing
            batch.status = 'DRAFT'
            batch.rejection_reason = None
            # Clear old results for re-entry
            Result.query.filter_by(batch_id=batch.id).delete()
        else:
            batch = ResultBatch(
                course_id=course_id,
                semester=semester,
                academic_session=academic_session,
                lecturer_id=current_user.id,
                status='DRAFT'
            )
            db.session.add(batch)
            db.session.flush()

        # Process each student's scores
        count = 0
        for student in students:
            ca_key = f'ca_{student.id}'
            exam_key = f'exam_{student.id}'
            ca_score = request.form.get(ca_key, 0, type=float)
            exam_score = request.form.get(exam_key, 0, type=float)

            # Validate score ranges
            ca_score = max(0, min(40, ca_score))
            exam_score = max(0, min(60, exam_score))

            total, grade, points = compute_result(ca_score, exam_score)

            result = Result(
                batch_id=batch.id,
                student_id=student.id,
                ca_score=ca_score,
                exam_score=exam_score,
                total_score=total,
                grade=grade,
                grade_point=points
            )
            db.session.add(result)
            count += 1

        db.session.commit()
        log_action(current_user.id, 'CREATE', 'ResultBatch', batch.id,
                   f'Uploaded {count} results for {course.code} ({academic_session})')
        flash(f'Results saved as draft. {count} student records processed.', 'success')
        return redirect(url_for('lecturer.dashboard'))

    return render_template('lecturer/upload_marks.html',
                           course=course, students=students)


@lecturer_bp.route('/batch/<int:batch_id>')
@login_required
@role_required('lecturer')
def view_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch or batch.lecturer_id != current_user.id:
        flash('Batch not found.', 'danger')
        return redirect(url_for('lecturer.dashboard'))

    results = batch.results.all()
    return render_template('lecturer/view_batch.html', batch=batch, results=results)


@lecturer_bp.route('/batch/<int:batch_id>/submit', methods=['POST'])
@login_required
@role_required('lecturer')
def submit_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch or batch.lecturer_id != current_user.id:
        flash('Batch not found.', 'danger')
        return redirect(url_for('lecturer.dashboard'))

    if batch.status != 'DRAFT':
        flash('Only draft batches can be submitted.', 'warning')
        return redirect(url_for('lecturer.dashboard'))

    if batch.results.count() == 0:
        flash('Cannot submit an empty batch.', 'danger')
        return redirect(url_for('lecturer.view_batch', batch_id=batch_id))

    batch.status = 'SUBMITTED'
    batch.submitted_at = datetime.utcnow()
    db.session.commit()

    log_action(current_user.id, 'SUBMIT', 'ResultBatch', batch.id,
               f'Submitted results for {batch.course.code} to HOD for approval')
    flash('Results submitted for HOD approval.', 'success')
    return redirect(url_for('lecturer.dashboard'))
