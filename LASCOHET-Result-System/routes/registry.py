from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, ResultBatch, Result, StudentProfile
from utils.decorators import role_required
from utils.audit import log_action
from utils.gpa import compute_semester_gpa

registry_bp = Blueprint('registry', __name__, template_folder='../templates/registry')


@registry_bp.route('/dashboard')
@login_required
@role_required('registry')
def dashboard():
    pending = ResultBatch.query.filter_by(status='HOD_APPROVED')\
        .order_by(ResultBatch.hod_approved_at.desc()).all()

    published = ResultBatch.query.filter_by(status='REGISTRY_APPROVED')\
        .order_by(ResultBatch.registry_approved_at.desc()).limit(20).all()

    return render_template('registry/dashboard.html',
                           pending_batches=pending, published_batches=published)


@registry_bp.route('/review/<int:batch_id>')
@login_required
@role_required('registry')
def review_results(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('registry.dashboard'))

    results = batch.results.all()
    return render_template('registry/review_results.html', batch=batch, results=results)


@registry_bp.route('/publish/<int:batch_id>', methods=['POST'])
@login_required
@role_required('registry')
def publish_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('registry.dashboard'))

    if batch.status != 'HOD_APPROVED':
        flash('Only HOD-approved batches can be published.', 'warning')
        return redirect(url_for('registry.dashboard'))

    batch.status = 'REGISTRY_APPROVED'
    batch.registry_officer_id = current_user.id
    batch.registry_approved_at = datetime.utcnow()
    db.session.commit()

    # Compute GPAs for all students in this batch
    student_ids = [r.student_id for r in batch.results.all()]
    for sid in student_ids:
        compute_semester_gpa(sid, batch.semester, batch.academic_session)

    log_action(current_user.id, 'PUBLISH', 'ResultBatch', batch.id,
               f'Registry published results for {batch.course.code} ({batch.academic_session})')
    flash('Results published! Students can now view them.', 'success')
    return redirect(url_for('registry.dashboard'))


@registry_bp.route('/reject/<int:batch_id>', methods=['POST'])
@login_required
@role_required('registry')
def reject_batch(batch_id):
    batch = db.session.get(ResultBatch, batch_id)
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('registry.dashboard'))

    if batch.status != 'HOD_APPROVED':
        flash('Only HOD-approved batches can be rejected here.', 'warning')
        return redirect(url_for('registry.dashboard'))

    reason = request.form.get('rejection_reason', '').strip()
    if not reason:
        flash('Please provide a reason for rejection.', 'danger')
        return redirect(url_for('registry.review_results', batch_id=batch_id))

    batch.status = 'REJECTED'
    batch.rejection_reason = reason
    batch.rejected_by_id = current_user.id
    batch.rejected_at = datetime.utcnow()
    db.session.commit()

    log_action(current_user.id, 'REJECT', 'ResultBatch', batch.id,
               f'Registry rejected results for {batch.course.code}: {reason}')
    flash('Results rejected and sent back for correction.', 'warning')
    return redirect(url_for('registry.dashboard'))
