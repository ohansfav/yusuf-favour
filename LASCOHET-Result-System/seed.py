"""Seed the database with initial LASCOHET data and demo accounts."""
from app import create_app
from models import db, User, Department, Program, Course, StudentProfile

app = create_app()

with app.app_context():
    db.create_all()

    # Skip if already seeded
    if User.query.first():
        print("Database already seeded. Skipping.")
        exit()

    # === Departments ===
    departments = [
        Department(name='Community Health', code='CHT'),
        Department(name='Pharmacy Technician', code='PHT'),
        Department(name='Medical Laboratory Technology', code='MLT'),
        Department(name='Environmental Health Technology', code='EHT'),
        Department(name='Health Information Management', code='HIM'),
        Department(name='Dental Health Technology', code='DHT'),
    ]
    db.session.add_all(departments)
    db.session.flush()

    dept_map = {d.code: d for d in departments}

    # === Programs ===
    programs = [
        Program(name='Community Health Extension Worker', code='CHEW', department_id=dept_map['CHT'].id, duration_years=3),
        Program(name='Pharmacy Technician', code='PHARM', department_id=dept_map['PHT'].id, duration_years=3),
        Program(name='Medical Lab Technician', code='MLAB', department_id=dept_map['MLT'].id, duration_years=3),
        Program(name='Environmental Health Officer', code='EHO', department_id=dept_map['EHT'].id, duration_years=3),
        Program(name='Health Records Officer', code='HRO', department_id=dept_map['HIM'].id, duration_years=3),
        Program(name='Dental Therapist', code='DENT', department_id=dept_map['DHT'].id, duration_years=3),
    ]
    db.session.add_all(programs)
    db.session.flush()

    prog_map = {p.code: p for p in programs}

    # === Users ===
    # Admin
    admin = User(username='admin', email='admin@lascohet.edu.ng',
                 full_name='System Administrator', role='admin')
    admin.set_password('admin123')

    # Registry
    registry = User(username='registry', email='registry@lascohet.edu.ng',
                    full_name='Mrs. Adebayo Folake', role='registry')
    registry.set_password('registry123')

    # HODs
    hod_cht = User(username='hod_cht', email='hod.cht@lascohet.edu.ng',
                   full_name='Dr. Ogunleye Adewale', role='hod',
                   department_id=dept_map['CHT'].id)
    hod_cht.set_password('hod123')

    hod_pht = User(username='hod_pht', email='hod.pht@lascohet.edu.ng',
                   full_name='Dr. Nwosu Chidinma', role='hod',
                   department_id=dept_map['PHT'].id)
    hod_pht.set_password('hod123')

    # Exam Officer
    exam_off = User(username='exam_officer', email='examofficer@lascohet.edu.ng',
                    full_name='Mr. Balogun Tunde', role='exam_officer',
                    department_id=dept_map['CHT'].id)
    exam_off.set_password('exam123')

    # Lecturers
    lec1 = User(username='lec_akin', email='akin@lascohet.edu.ng',
                full_name='Mr. Akinwale Ibrahim', role='lecturer',
                department_id=dept_map['CHT'].id)
    lec1.set_password('lecturer123')

    lec2 = User(username='lec_ngozi', email='ngozi@lascohet.edu.ng',
                full_name='Mrs. Ngozi Eze', role='lecturer',
                department_id=dept_map['PHT'].id)
    lec2.set_password('lecturer123')

    db.session.add_all([admin, registry, hod_cht, hod_pht, exam_off, lec1, lec2])
    db.session.flush()

    # === Courses ===
    courses = [
        # Community Health - Level 100
        Course(code='CHT101', title='Introduction to Community Health', credit_units=3,
               semester='First', level=100, program_id=prog_map['CHEW'].id, lecturer_id=lec1.id),
        Course(code='CHT102', title='Primary Health Care', credit_units=3,
               semester='First', level=100, program_id=prog_map['CHEW'].id, lecturer_id=lec1.id),
        Course(code='CHT103', title='Human Anatomy & Physiology I', credit_units=4,
               semester='First', level=100, program_id=prog_map['CHEW'].id, lecturer_id=lec1.id),
        Course(code='CHT104', title='Health Education', credit_units=2,
               semester='Second', level=100, program_id=prog_map['CHEW'].id, lecturer_id=lec1.id),
        Course(code='CHT105', title='Human Anatomy & Physiology II', credit_units=4,
               semester='Second', level=100, program_id=prog_map['CHEW'].id, lecturer_id=lec1.id),

        # Pharmacy Technician - Level 100
        Course(code='PHT101', title='Introduction to Pharmacy', credit_units=3,
               semester='First', level=100, program_id=prog_map['PHARM'].id, lecturer_id=lec2.id),
        Course(code='PHT102', title='Pharmaceutical Chemistry I', credit_units=3,
               semester='First', level=100, program_id=prog_map['PHARM'].id, lecturer_id=lec2.id),
        Course(code='PHT103', title='Pharmacology I', credit_units=4,
               semester='Second', level=100, program_id=prog_map['PHARM'].id, lecturer_id=lec2.id),
    ]
    db.session.add_all(courses)
    db.session.flush()

    # === Students ===
    students_data = [
        ('stu_amina', 'amina@student.lascohet.edu.ng', 'Amina Yusuf', 'LCH/2025/001', 'CHEW', 100, 2025),
        ('stu_chidi', 'chidi@student.lascohet.edu.ng', 'Chidi Okafor', 'LCH/2025/002', 'CHEW', 100, 2025),
        ('stu_fatima', 'fatima@student.lascohet.edu.ng', 'Fatima Abdullahi', 'LCH/2025/003', 'CHEW', 100, 2025),
        ('stu_bola', 'bola@student.lascohet.edu.ng', 'Bola Adeyemi', 'LCH/2025/004', 'CHEW', 100, 2025),
        ('stu_emeka', 'emeka@student.lascohet.edu.ng', 'Emeka Nnamdi', 'LCH/2025/005', 'CHEW', 100, 2025),
        ('stu_kemi', 'kemi@student.lascohet.edu.ng', 'Kemi Adeola', 'LCH/2025/101', 'PHARM', 100, 2025),
        ('stu_uche', 'uche@student.lascohet.edu.ng', 'Uche Ikenna', 'LCH/2025/102', 'PHARM', 100, 2025),
        ('stu_halima', 'halima@student.lascohet.edu.ng', 'Halima Sani', 'LCH/2025/103', 'PHARM', 100, 2025),
    ]

    for uname, email, fname, matric, prog_code, level, year in students_data:
        user = User(username=uname, email=email, full_name=fname, role='student')
        user.set_password('student123')
        db.session.add(user)
        db.session.flush()

        profile = StudentProfile(
            user_id=user.id,
            matric_number=matric,
            program_id=prog_map[prog_code].id,
            level=level,
            admission_year=year
        )
        db.session.add(profile)

    db.session.commit()

    print("=" * 50)
    print("  LASCOHET Database Seeded Successfully!")
    print("=" * 50)
    print()
    print("  Demo Login Credentials:")
    print("  ─────────────────────────────────────")
    print("  Admin:        admin / admin123")
    print("  Registry:     registry / registry123")
    print("  HOD (CHT):    hod_cht / hod123")
    print("  HOD (PHT):    hod_pht / hod123")
    print("  Exam Officer: exam_officer / exam123")
    print("  Lecturer 1:   lec_akin / lecturer123")
    print("  Lecturer 2:   lec_ngozi / lecturer123")
    print("  Student:      stu_amina / student123")
    print("  (All students use password: student123)")
    print("  ─────────────────────────────────────")
    print()
