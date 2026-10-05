from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    # Roles: student, lecturer, hod, exam_officer, registry, admin
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = db.relationship('Department', backref='staff')
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    programs = db.relationship('Program', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.code}>'


class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    duration_years = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course', backref='program', lazy='dynamic')
    students = db.relationship('StudentProfile', backref='program', lazy='dynamic')

    def __repr__(self):
        return f'<Program {self.code}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    credit_units = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.String(10), nullable=False)  # 'First' or 'Second'
    level = db.Column(db.Integer, nullable=False)  # 100, 200, 300
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lecturer = db.relationship('User', backref='courses_taught')
    result_batches = db.relationship('ResultBatch', backref='course', lazy='dynamic')

    def __repr__(self):
        return f'<Course {self.code}>'


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    matric_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    level = db.Column(db.Integer, default=100)
    admission_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('Result', backref='student_profile', lazy='dynamic')

    def __repr__(self):
        return f'<Student {self.matric_number}>'


class ResultBatch(db.Model):
    """Represents a batch of results for a course in a session/semester.
    Tracks the multi-level approval workflow."""
    __tablename__ = 'result_batches'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    academic_session = db.Column(db.String(20), nullable=False)  # e.g. '2025/2026'
    lecturer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Workflow state: DRAFT -> SUBMITTED -> HOD_APPROVED -> REGISTRY_APPROVED | REJECTED
    status = db.Column(db.String(20), default='DRAFT', nullable=False)

    submitted_at = db.Column(db.DateTime, nullable=True)
    hod_approved_at = db.Column(db.DateTime, nullable=True)
    hod_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    registry_approved_at = db.Column(db.DateTime, nullable=True)
    registry_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    rejected_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lecturer = db.relationship('User', foreign_keys=[lecturer_id], backref='uploaded_batches')
    hod = db.relationship('User', foreign_keys=[hod_id])
    registry_officer = db.relationship('User', foreign_keys=[registry_officer_id])
    rejected_by = db.relationship('User', foreign_keys=[rejected_by_id])
    results = db.relationship('Result', backref='batch', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ResultBatch {self.course.code if self.course else "?"} - {self.status}>'


class Result(db.Model):
    """Individual student result within a batch."""
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('result_batches.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    ca_score = db.Column(db.Float, nullable=False, default=0)    # Continuous Assessment (max 40)
    exam_score = db.Column(db.Float, nullable=False, default=0)  # Exam score (max 60)
    total_score = db.Column(db.Float, nullable=False, default=0)
    grade = db.Column(db.String(5), nullable=True)
    grade_point = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('batch_id', 'student_id', name='unique_student_batch'),
    )

    def __repr__(self):
        return f'<Result Student:{self.student_id} Score:{self.total_score}>'


class SemesterGPA(db.Model):
    """Cached semester GPA for quick retrieval."""
    __tablename__ = 'semester_gpas'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    academic_session = db.Column(db.String(20), nullable=False)
    gpa = db.Column(db.Float, nullable=False)
    total_credits = db.Column(db.Integer, nullable=False)
    total_grade_points = db.Column(db.Float, nullable=False)
    academic_standing = db.Column(db.String(30), nullable=True)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('StudentProfile', backref='semester_gpas')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'semester', 'academic_session', name='unique_student_semester'),
    )


class AuditLog(db.Model):
    """Immutable audit trail for all system actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, APPROVE, REJECT, etc.
    entity_type = db.Column(db.String(50), nullable=True)  # User, Result, ResultBatch, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AuditLog {self.action} by User:{self.user_id} at {self.timestamp}>'
