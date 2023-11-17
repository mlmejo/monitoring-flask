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
from model import Attendance, Schedule, Student, Subject, Teacher, Secrets

load_dotenv()

schedules_blueprint = flask.Blueprint("schedules", __name__)


@schedules_blueprint.route("/schedules", strict_slashes=False)
@flask_login.login_required
def list_():
    schedules = None

    if flask_login.current_user.role == "teacher":
        teacher = Teacher.query.filter_by(user_id=flask_login.current_user.id).first()
        schedules = teacher.schedules
    else:
        schedules = Schedule.query.all()

    return flask.render_template("schedules/index.html", schedules=schedules)


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
        flask.flash(f"{field}: The field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/schedules")

    try:
        schedule = Schedule(
            section=data.get("section"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
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

    if student.face_id(flask.request.files["image"]):
        student.check_in(schedule_id)
        return flask.render_template("attendance-success.html", message="Attendance recorded.", category="success")
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
