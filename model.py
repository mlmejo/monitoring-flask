import bcrypt
from flask_login import UserMixin
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import Integer, LargeBinary, String

from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(255), nullable=False)
    email = db.Column(String(255), unique=True, nullable=False)
    password = db.Column(LargeBinary, nullable=False)

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


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), unique=True, nullable=False)


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", cascade="all", lazy=True)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", cascade="all", lazy=True)

    def check_in(self, schedule_id):
        schedule = Schedule.query.get_or_404(schedule_id)
        attendance = Attendance(schedule=schedule, student=self)

        db.session.add(attendance)
        db.session.commit()


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
    section = db.Column(String(255), nullable=False)
    teacher_id = db.Column(
        Integer,
        db.ForeignKey("teachers.id"),
        nullable=False,
    )
    teacher = db.relationship(
        "Teacher",
        cascade="all",
        lazy=True,
    )
    subject_id = db.Column(
        Integer,
        db.ForeignKey("subjects.id"),
        nullable=False,
    )
    subject = db.relationship(
        "Subject",
        cascade="all",
        lazy=True,
    )
    students = db.relationship(
        "Student",
        secondary=schedule_student,
        backref="schedules",
    )

    __table_args__ = (
        UniqueConstraint(
            "section",
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
