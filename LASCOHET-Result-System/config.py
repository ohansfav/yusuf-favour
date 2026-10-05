import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with security-by-design principles."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'lascohet.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # CSRF protection enabled by default via Flask-WTF
    WTF_CSRF_ENABLED = True

    # Institution info
    INSTITUTION_NAME = "Lagos State College of Health Technology"
    INSTITUTION_SHORT = "LASCOHET"

    # LASCOHET Grading Scale (Health Technology Programs)
    GRADING_SCALE = [
        {'grade': 'A',  'min': 70, 'max': 100, 'points': 4.0},
        {'grade': 'AB', 'min': 60, 'max': 69,  'points': 3.5},
        {'grade': 'B',  'min': 50, 'max': 59,  'points': 3.0},
        {'grade': 'BC', 'min': 45, 'max': 49,  'points': 2.5},
        {'grade': 'C',  'min': 40, 'max': 44,  'points': 2.0},
        {'grade': 'CD', 'min': 35, 'max': 39,  'points': 1.5},
        {'grade': 'D',  'min': 30, 'max': 34,  'points': 1.0},
        {'grade': 'F',  'min': 0,  'max': 29,  'points': 0.0},
    ]

    # Academic Standing Thresholds
    ACADEMIC_STANDING = [
        {'standing': 'Distinction',   'min_gpa': 3.50, 'max_gpa': 4.00},
        {'standing': 'Upper Credit',  'min_gpa': 3.00, 'max_gpa': 3.49},
        {'standing': 'Lower Credit',  'min_gpa': 2.50, 'max_gpa': 2.99},
        {'standing': 'Pass',          'min_gpa': 2.00, 'max_gpa': 2.49},
        {'standing': 'Fail',          'min_gpa': 0.00, 'max_gpa': 1.99},
    ]

    # Approval workflow states
    WORKFLOW_STATES = ['DRAFT', 'SUBMITTED', 'HOD_APPROVED', 'REGISTRY_APPROVED', 'REJECTED']
