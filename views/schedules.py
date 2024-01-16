import base64
import datetime
import io
import secrets
import os

import flask
import flask_login
import qrcode
from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import config
from extensions import db
from lib import request_input
from model import Attendance, Course, Schedule, Student, Subject, Teacher, Secrets

load_dotenv()

schedules_blueprint = flask.Blueprint("schedules", __name__)


# @schedules_blueprint.route("/teachers/<int:teacher_id>/schedules", strict_slashes=False)
# @flask_login.login_required
# def list_(teacher_id):
#     teacher_id = Teacher.query.get_or_404(teacher_id)
#     schedules = None

#     if flask_login.current_user.role == "teacher":
#         teacher = Teacher.query.filter_by(user_id=flask_login.current_user.id).first()
#         schedules = teacher.schedules
#     else:
#         schedules = Schedule.query.all()

#     return flask.render_template("schedules/index.html", schedules=schedules)
@schedules_blueprint.route(
    "/teachers/<int:teacher_id>/schedules",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def list_(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    handled_subjects = [schedule.subject for schedule in teacher.schedules]

    if flask.request.method == "POST":
        data = {
            "school_year": request_input("school_year"),
            "day": request_input("day"),
            "semester": request_input("semester"),
            "year_level": request_input("year_level"),
            "course_id": request_input("course_id"),
            "subject_id": request_input("subject_id"),
            "time_start": request_input("time_start"),
            "time_end": request_input("time_end"),
            "room": request_input("room"),
        }

        errors = []
        for field, value in data.items():
            if value is not None:
                continue
            errors.append(f"{field}: The field is required.")

        if errors:
            return flask.redirect(
                flask.url_for("schedules.list_", teacher_id=teacher_id, errors=errors)
            )

        course = Course.query.get_or_404(data["course_id"])
        subject = Subject.query.get_or_404(data["subject_id"])

        schedule = Schedule(
            school_year=data["school_year"],
            day=data["day"],
            semester=data["semester"],
            year_level=data["year_level"],
            teacher=teacher,
            course=course,
            subject=subject,
            time_start=data["time_start"],
            time_end=data["time_end"],
            room=data["room"],
        )
        db.session.add(schedule)
        db.session.commit()

        flask.flash("Schedule has been created.", "success")
        return flask.redirect(flask.request.referrer)

    teacher = Teacher.query.get_or_404(teacher_id)
    subjects = Subject.query.all()
    courses = Course.query.all()
    return flask.render_template(
        "schedules/index.html",
        teacher=teacher,
        subjects=subjects,
        courses=courses,
        handled_subjects=handled_subjects,
    )


@schedules_blueprint.post(
    "/teachers/<int:teacher_id>/schedules/remove-schedule",
    strict_slashes=False
)
@flask_login.login_required
def remove_schedule(teacher_id):
    if flask.request.method == "POST":
        teacher = Teacher.query.get_or_404(teacher_id)
        data = {
            "subject_id": request_input("subject_id"),
        }

        errors = []
        for field, value in data.items():
            if value is not None:
                continue
            errors.append(f"{field}: The field is required.")

        if errors:
            return flask.redirect(
                flask.url_for("schedules.list_", teacher_id=teacher_id, errors=errors)
            )

        subject = Subject.query.get_or_404(data["subject_id"])
        schedule = Schedule.query.filter_by(teacher=teacher, subject=subject).first()
        db.session.delete(schedule)
        db.session.commit()

        flask.flash("Removed schedule.", "success")

    return flask.redirect(flask.url_for("schedules.list_", teacher_id=teacher_id))

@schedules_blueprint.route(
    "/schedules/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def create_schedule():
    if flask.request.method == "GET":
        subjects = Subject.query.all()
        teachers = Teacher.query.all()

        return flask.render_template(
            "schedules/create.html",
            subjects=subjects,
            teachers=teachers,
        )

    data = {
        "school_year": request_input("school_year"),
        "day": request_input("day"),
        "semester": request_input("semester"),
        "year_level": request_input("year_level"),
        "course_id": request_input("course_id"),
        "subject_id": request_input("subject_id"),
        "teacher_id": request_input("teacher_id"),
    }

    course = Course.query.get_or_404(data.get("course_id"))
    subject = Subject.query.get_or_404(data.get("subject_id"))
    teacher = Teacher.query.get_or_404(data.get("teacher_id"))

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: The field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/schedules")

    try:
        schedule = Schedule(
            school_year=data.get("school_year"),
            day=data.get("day"),
            semester=data.get("semester"),
            year_level=data.get("year_level"),
            course=course,
            subject=subject,
            teacher=teacher,
        )
        db.session.add(schedule)
        db.session.commit()
    except IntegrityError:
        flask.flash(
            "Schedule with identical details already exists.",
            "danger",
        )
    else:
        flask.flash("Schedule created successfully.", "success")

    return flask.redirect("/schedules")


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def schedule_delete(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)

    if flask.request.method == "POST":
        db.session.delete(schedule)
        db.session.commit()

        flask.flash(
            "Schedule deleted successfully.",
            "danger",
        )
        return flask.redirect("/schedules")

    return flask.render_template(
        "schedules/delete.html",
        schedule=schedule,
    )


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def update(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    teachers = Teacher.query.all()
    subjects = Subject.query.all()

    if flask.request.method == "GET":
        return flask.render_template(
            "schedules/edit.html",
            schedule=schedule,
            subjects=subjects,
            teachers=teachers
        )

    data = {
        "section": request_input("section"),
        "start_time": request_input("start_time"),
        "end_time": request_input("end_time"),
        "subject_id": request_input("subject_id"),
        "teacher_id": request_input("teacher_id"),
    }

    subject = Subject.query.get_or_404(data.get("subject_id"))
    teacher = Teacher.query.get_or_404(data.get("teacher_id"))

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: This field is required", "danger")
        error = True

    if error:
        flask.flash(
            "Another schedule with these details already exists.",
            "danger",
        )
        return flask.redirect("/schedules")

    schedule.start_time = data.get("start_time")
    schedule.end_time = data.get("end_time")
    schedule.subject = subject
    schedule.teacher = teacher

    db.session.commit()

    flask.flash("Schedule updated successfully.", "success")

    return flask.redirect("/schedules")


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def schedule_details(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    return flask.render_template("schedules/show.html", schedule=schedule)


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/generate-qrcode", strict_slashes=False
)
@flask_login.login_required
def generate_qr(schedule_id):
    ip_addr = os.getenv("IP_ADDRESS")
    secret = Secrets(token=secrets.token_hex())
    db.session.add(secret)
    db.session.commit()

    result = qrcode.make(
        f"http://{ip_addr}:5000/"
        + flask.url_for("schedules.record_attendance", schedule_id=schedule_id, token=secret.token)
    )
    buffer = io.BytesIO()

    result.save(buffer, "PNG")
    buffer.seek(0)

    data = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()

    return data


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/record-attendance/<token>",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def record_attendance(schedule_id, token):
    secret = Secrets.query.filter_by(token=token).first()

    if not secret:
        return flask.abort(403)

    if flask_login.current_user and flask_login.current_user.role != "student":
        return flask.abort(403)

    schedule = Schedule.query.get_or_404(schedule_id)

    if flask.request.method == "GET":
        return flask.render_template(
            "schedules/record_attendance.html",
            schedule=schedule,
        )

    student = Student.query.filter_by(user=flask_login.current_user).first()
    attendance = Attendance.query.filter_by(secret=token).first()

    if student.face_id(flask.request.files["image"]) and attendance is None:
        student.check_in(schedule_id)
        return flask.render_template("attendance-success.html", message="Attendance recorded.", category="success")
    elif attendance is not None:
        attendance.time_out = datetime.datetime.now()
        db.session.commit()
    else:
        return flask.render_template("attendance-failed.html", message="Face recognition failed.", categry="danger")


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/students/",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def schedule_students(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)

    if flask.request.method == "POST":
        data = {
            "student_id": request_input("student_id"),
        }

        errors = False
        for field, value in data.items():
            if value is None:
                flask.flash(f"{field}: The field is required.", "danger")

        if errors:
            return flask.redirect(
                flask.url_for(
                    "schedules.schedule_students",
                    schedule_id=schedule_id,
                )
            )

        student = Student.query.get_or_404(data.get("student_id"))
        schedule.students.append(student)

        flask.flash(f"{student.user.name} added successfully.", "success")
        db.session.commit()

    students = Student.query.all()
    return flask.render_template(
        "schedules/student_list.html",
        schedule=schedule,
        students=students,
    )


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/attendances",
    strict_slashes=False,
)
def attendance_list(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    date_str = flask.request.args.get("date")
    date = None

    if date_str:
        date = datetime.datetime.strptime(date_str, "%B %d, %Y, %I:%M %p")
    else:
        date = datetime.datetime.now()

    attendances = []

    for q in Attendance.query.filter_by(schedule=schedule):
        if q.time_in.date() == date.date():
            attendances.append(q)

    return flask.render_template(
        "attendances/index.html",
        schedule=schedule,
        attendances=attendances,
    )


@schedules_blueprint.route(
    "/students/<int:student_id>/schedules",
    methods=["GET", "POST"],
    strict_slashes=False
)
def student_schedules(student_id):
    student = Student.query.get_or_404(student_id)
    schedules = Schedule.query.all()
    student_load = [schedule.subject for schedule in student.schedules]

    if flask.request.method == "POST":
        data = {
            "schedule_id": request_input("schedule_id"),
        }

        errors = []
        for field, value in data.items():
            if value is not None:
                continue
            flask.flash(f"{field}: The field is required.")

        if errors:
            return flask.redirect(
                flask.request.referrer
            )

        student = Student.query.get_or_404(student_id)
        schedule = Schedule.query.get_or_404(data["schedule_id"])
        schedule.students.append(student)

        db.session.commit()

        return flask.redirect(flask.request.referrer)

    return flask.render_template(
        "student_schedules.html",
        student=student,
        schedules=schedules,
        student_load=student_load,
    )


@schedules_blueprint.post(
    "/students/<int:student_id>/schedules/remove-schedule",
    strict_slashes=False
)
def remove_student_schedule(student_id):
    data = {
        "schedule_id": request_input("schedule_id"),
    }

    errors = []
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: The field is required.")

    if errors:
        return flask.redirect(
            flask.request.referrer
        )

    student = Student.query.get_or_404(student_id)
    schedule = Schedule.query.get_or_404(data["schedule_id"])
    schedule.students.remove(student)

    db.session.commit()

    return flask.redirect(flask.url_for("schedules.student_schedules", student_id=student_id))


@schedules_blueprint.route(
    "/teachers/<int:teacher_id>/schedules/show",
    strict_slashes=False
)
def teacher_schedule_show(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    schedules = []

    for schedule in teacher.schedules:
        schedule.time_start = datetime.datetime.strptime(schedule.time_start, "%H:%M")
        schedule.time_end = datetime.datetime.strptime(schedule.time_end, "%H:%M")
        schedules.append(schedule)

    return flask.render_template('teachers/schedule.html', teacher=teacher, schedules=schedules)


@schedules_blueprint.route(
    '/teachers-schedules',
    strict_slashes=False
)
def teachers_schedules():
    teachers = Teacher.query.all()
    return flask.render_template('teachers/schedules.html', teachers=teachers)
