import flask

from sqlalchemy.exc import IntegrityError

from extensions import db
from lib import request_input
from model import Schedule, Subject, Teacher

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

    schedule.subject = subject
    schedule.teacher = teacher

    return flask.redirect("/schedules")
