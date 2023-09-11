import base64
import io
import secrets

import flask
import qrcode
from sqlalchemy.exc import IntegrityError

from extensions import db
from lib import request_input
from model import Schedule, Student, Subject, Teacher

schedules_blueprint = flask.Blueprint("schedules", __name__)


@schedules_blueprint.route("/schedules", strict_slashes=False)
def list_():
    schedules = Schedule.query.all()
    return flask.render_template("schedules/index.html", schedules=schedules)


@schedules_blueprint.route(
    "/schedules/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
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
    "/subjects/<int:schedule_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def update(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)

    if flask.request.method == "GET":
        return flask.render_template(
            "schedule/edit.html",
            schedule=schedule,
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
def schedule_details(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    return flask.render_template("schedules/show.html", schedule=schedule)


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/generate-qrcode", strict_slashes=False
)
def generate_qr(schedule_id):
    result = qrcode.make(
        "http://localhost:5000"
        + flask.url_for("schedules.record_attendance", schedule_id=schedule_id)
        + "?secret={}".format(secrets.token_hex()),
    )
    buffer = io.BytesIO()

    result.save(buffer, "PNG")
    buffer.seek(0)

    data = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()

    return data


@schedules_blueprint.route(
    "/schedules<int:schedule_id>/record-attendance",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def record_attendance():
    return flask.render_template("schedules/record_attendance.html")


@schedules_blueprint.route(
    "/schedules/<int:schedule_id>/students/",
    methods=["GET", "POST"],
    strict_slashes=False,
)
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