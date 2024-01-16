import io
import os
from datetime import datetime

import bcrypt
import face_recognition
import flask
import flask_login
import numpy as np
import PIL
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import DateTime, Integer, LargeBinary, String

from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, flask_login.UserMixin):
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False)
    email = db.Column(String(255), unique=True, nullable=False)
    password = db.Column(LargeBinary, nullable=False)
    role = db.Column(String(16), nullable=False)

    def set_password(self, password):
        self.password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        )

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password)

    @staticmethod
    def filter_by_email(email):
        return User.query.filter_by(email=email)


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", cascade="all", lazy=True)


course_subject = db.Table(
    "course_subject",
    db.Column("id", Integer, primary_key=True),
    db.Column(
        "course_id",
        Integer,
        db.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "subject_id",
        Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("course_id", "subject_id"),
)


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), unique=True, nullable=False)
    course_number = db.Column(String(16), unique=True, nullable=False)
    lec_hours = db.Column(Integer, nullable=False)
    lab_hours = db.Column(Integer, nullable=False)
    units = db.Column(db.Integer, nullable=False)
    year_level = db.Column(String(64), nullable=False)
    semester = db.Column(String(64), nullable=False)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), unique=True, nullable=False)
    students = db.relationship(
        "Student",
        backref="course",
    )
    subjects = db.relationship(
        "Subject",
        secondary="course_subject",
        backref="courses",
    )


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(Integer, primary_key=True)
    image_filename = db.Column(String(255), nullable=False)
    user_id = db.Column(Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(Integer, db.ForeignKey("courses.id"), nullable=False)

    user = db.relationship("User", cascade="all", lazy=True)

    def check_in(self, schedule_id):
        schedule = Schedule.query.get_or_404(schedule_id)
        time_start = datetime.strptime(schedule.time_start, '%H:%M').time()
        current_time = datetime.now().time()

        diff = datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(), time_start)

        is_late = diff.total_seconds() > 15 * 60

        if is_late:
            attendance = Attendance(schedule=schedule, student=self, status="Present")
        else:
            attendance = Attendance(schedule=schedule, student=self)

        db.session.add(attendance)
        db.session.commit()

    def face_id(self, uploaded_image):
        profile = face_recognition.load_image_file(
            os.path.join(
                flask.current_app.config["UPLOAD_FOLDER"],
                self.image_filename.replace(" ", "_"),
            ),
        )
        profile_encoding = face_recognition.face_encodings(profile, num_jitters=100)[0]

        buffer = PIL.Image.open(io.BytesIO(uploaded_image.read()))
        buffer = buffer.convert("RGB")

        face_locations = face_recognition.face_locations(np.array(buffer))

        if not face_locations:
            return False

        upload_encoding = face_recognition.face_encodings(
            np.array(buffer), face_locations, num_jitters=100
        )[0]

        result = face_recognition.compare_faces(
            [profile_encoding], upload_encoding, tolerance=0.5
        )[0]

        return True if result else None


schedule_student = db.Table(
    "schedule_student",
    db.Column("id", Integer, primary_key=True),
    db.Column(
        "schedule_id",
        Integer,
        db.ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "student_id",
        Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    ),
    UniqueConstraint("schedule_id", "student_id"),
)


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(Integer, primary_key=True)
    school_year = db.Column(String(255), nullable=False)
    semester = db.Column(String(255), nullable=False)
    day = db.Column(String(255), nullable=False)
    year_level = db.Column(String(255), nullable=False)
    time_start = db.Column(String(64), nullable=False)
    time_end = db.Column(String(64), nullable=False)
    room = db.Column(String(32), nullable=False)
    status = db.Column(String(64), server_default="Present (incomplete)")
    course_id = db.Column(Integer, db.ForeignKey("courses.id"), nullable=False)
    course = db.relationship(
        "Course",
        lazy=True,
    )
    teacher_id = db.Column(
        Integer,
        db.ForeignKey("teachers.id"),
        nullable=False,
    )
    teacher = db.relationship(
        "Teacher",
        lazy=True,
        backref="schedules",
    )
    subject_id = db.Column(
        Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
    )
    subject = db.relationship(
        "Subject",
        lazy=True,
    )
    students = db.relationship(
        "Student",
        secondary=schedule_student,
        backref="schedules",
    )

    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "subject_id",
        ),
    )


class Attendance(db.Model):
    __tablename__ = "attendances"

    id = db.Column(Integer, primary_key=True)
    schedule_id = db.Column(
        Integer,
        db.ForeignKey("schedules.id", ondelete="CASCADE"),
    )
    schedule = db.relationship("Schedule", lazy=True)
    student_id = db.Column(
        Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
    )
    student = db.relationship("Student", lazy=True)
    time_in = db.Column(DateTime, default=datetime.now())
    time_out = db.Column(DateTime)
    secret_id = db.Column(Integer, db.ForeignKey('secrets.id'), nullable=False)
    secret = db.relationship('Secrets', lazy=True)


class Secrets(db.Model):
    __tablename__ = "secrets"

    id = db.Column(Integer, primary_key=True)
    token = db.Column(String(1024), unique=True, nullable=False)
