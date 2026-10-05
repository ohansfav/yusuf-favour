from flask import current_app
from models import db, Result, SemesterGPA, StudentProfile, ResultBatch, Course
from config import Config


def get_grade_and_points(total_score):
    """Return (grade, grade_point) for a given total score using LASCOHET scale."""
    for entry in Config.GRADING_SCALE:
        if entry['min'] <= total_score <= entry['max']:
            return entry['grade'], entry['points']
    return 'F', 0.0


def compute_result(ca_score, exam_score):
    """Compute total, grade, and grade point for a single result."""
    total = round(ca_score + exam_score, 2)
    total = min(total, 100.0)
    grade, points = get_grade_and_points(total)
    return total, grade, points


def compute_semester_gpa(student_id, semester, academic_session):
    """Compute and cache the semester GPA for a student.
    Only counts results from REGISTRY_APPROVED batches."""
    student = db.session.get(StudentProfile, student_id)
    if not student:
        return None

    # Get all approved results for this student in this semester/session
    results = (
        db.session.query(Result, Course)
        .join(ResultBatch, Result.batch_id == ResultBatch.id)
        .join(Course, ResultBatch.course_id == Course.id)
        .filter(
            Result.student_id == student_id,
            ResultBatch.semester == semester,
            ResultBatch.academic_session == academic_session,
            ResultBatch.status == 'REGISTRY_APPROVED'
        )
        .all()
    )

    if not results:
        return None

    total_credits = 0
    total_weighted_points = 0

    for result, course in results:
        credits = course.credit_units
        total_credits += credits
        total_weighted_points += (result.grade_point or 0) * credits

    if total_credits == 0:
        return None

    gpa = round(total_weighted_points / total_credits, 2)
    standing = get_academic_standing(gpa)

    # Upsert semester GPA
    existing = SemesterGPA.query.filter_by(
        student_id=student_id,
        semester=semester,
        academic_session=academic_session
    ).first()

    if existing:
        existing.gpa = gpa
        existing.total_credits = total_credits
        existing.total_grade_points = total_weighted_points
        existing.academic_standing = standing
    else:
        record = SemesterGPA(
            student_id=student_id,
            semester=semester,
            academic_session=academic_session,
            gpa=gpa,
            total_credits=total_credits,
            total_grade_points=total_weighted_points,
            academic_standing=standing
        )
        db.session.add(record)

    db.session.commit()
    return gpa


def compute_cgpa(student_id):
    """Compute cumulative GPA across all semesters."""
    records = SemesterGPA.query.filter_by(student_id=student_id).all()
    if not records:
        return 0.0, 'N/A'

    total_credits = sum(r.total_credits for r in records)
    total_points = sum(r.total_grade_points for r in records)

    if total_credits == 0:
        return 0.0, 'N/A'

    cgpa = round(total_points / total_credits, 2)
    standing = get_academic_standing(cgpa)
    return cgpa, standing


def get_academic_standing(gpa):
    """Return academic standing string based on GPA."""
    for entry in Config.ACADEMIC_STANDING:
        if entry['min_gpa'] <= gpa <= entry['max_gpa']:
            return entry['standing']
    return 'Fail'
