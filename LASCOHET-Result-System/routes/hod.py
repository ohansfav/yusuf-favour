from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, ResultBatch, Course, Department
from utils.decorators import role_required
from utils.audit import log_action

hod_bp = Blueprint('hod', __name__, template_folder='../templates/hod')


@hod_bp.route('/dashboard')
@login_required
@role_required('hod', 'exam_officer')
def dashboard():
    # HOD sees batches from their department
    dept_id = current_user.department_id

    pending = (
        ResultBatch.query
        .join(Course, ResultBatch.course_id == Course.id)
        .filter(ResultBatch.status == 'SUBMITTED')
    )

    if dept_id:
        from models import Program
        dept_programs = [p.id for p in Program.query.filter_by(department_id=dept_id).all()]
        pending = pending.filter(Course.program_id.in_(dept_programs))

    pending_batches = pending.order_by(ResultBatch.submitted_at.desc()).all()

    approved = (
        ResultBatch.query.filter_by(hod_id=current_user.id)
        .order_by(ResultBatch.hod_approved_at.desc()).limit(20).all()
    )

    return render_template('hod/dashboard.html',
                           pending_batches=pending_batches,
                           approved_batches=approved)


@hod_bp.route('/review/<int:batch_id>')
@login_required
@role_required('hod', 'exam_officer')
def review_results(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('hod.dashboard'))

    results = batch.results.all()
    return render_template('hod/review_results.html', batch=batch, results=results)


@hod_bp.route('/approve/<int:batch_id>', methods=['POST'])
@login_required
@role_required('hod', 'exam_officer')
def approve_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('hod.dashboard'))

    if batch.status != 'SUBMITTED':
        flash('Only submitted batches can be approved at this level.', 'warning')
        return redirect(url_for('hod.dashboard'))

    batch.status = 'HOD_APPROVED'
    batch.hod_id = current_user.id
    batch.hod_approved_at = datetime.utcnow()
    db.session.commit()

    log_action(current_user.id, 'APPROVE', 'ResultBatch', batch.id,
               f'HOD approved results for {batch.course.code} ({batch.academic_session})')
    flash('Results approved and forwarded to Registry.', 'success')
    return redirect(url_for('hod.dashboard'))


@hod_bp.route('/reject/<int:batch_id>', methods=['POST'])
@login_required
@role_required('hod', 'exam_officer')
def reject_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('hod.dashboard'))

    if batch.status != 'SUBMITTED':
        flash('Only submitted batches can be rejected.', 'warning')
        return redirect(url_for('hod.dashboard'))

    reason = request.form.get('rejection_reason', '').strip()
    if not reason:
        flash('Please provide a reason for rejection.', 'danger')
        return redirect(url_for('hod.review_results', batch_id=batch_id))

    batch.status = 'REJECTED'
    batch.rejection_reason = reason
    batch.rejected_by_id = current_user.id
    batch.rejected_at = datetime.utcnow()
    db.session.commit()

    log_action(current_user.id, 'REJECT', 'ResultBatch', batch.id,
               f'HOD rejected results for {batch.course.code}: {reason}')
    flash('Results rejected and sent back to lecturer.', 'warning')
    return redirect(url_for('hod.dashboard'))
