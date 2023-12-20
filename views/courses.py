import flask
import flask_login

from extensions import db
from lib import request_input
from model import Course

courses_blueprint = flask.Blueprint("courses", __name__)


@courses_blueprint.get("/courses", strict_slashes=False)
@flask_login.login_required
def list_():
    courses = Course.query.all()
    return flask.render_template("courses/index.html", courses=courses)


@courses_blueprint.route(
    "/courses/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def create_course():
    if flask.request.method == "GET":
        return flask.render_template("courses/create.html")

    data = {
        "name": request_input("name")
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: The field is required", "danger")
        error = True

    if error:
        return flask.redirect("/courses")

    exists = Course.query.filter_by(name=data.get("name")).first()

    if exists:
        flask.flash("Course with name already exists.", "danger")
        return flask.redirect("/courses")

    course = Course(**data)
    db.session.add(course)
    db.session.commit()

    flask.flash("Course has been created.", "success")

    return flask.redirect("/courses")


@courses_blueprint.route(
    "/courses/<int:course_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False
)
@flask_login.login_required
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)

    if flask.request.method == "POST":
        flask.flash(f"{course.name} deleted successfully.", "success")

        db.session.delete(course)
        db.session.commit()

        return flask.redirect("/courses")

    return flask.render_template("courses/delete.html", course=course)

@courses_blueprint.route(
    "/courses/<int:course_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def update(course_id):
    course = Course.query.get_or_404(course_id)

    if flask.request.method == "GET":
        return flask.render_template("courses/edit.html", course=course)

    data = {
        "name": request_input("name"),
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: This field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/courses")

    exists = Course.query.filter_by(name=data.get("name")).first()

    if exists and not exists.name == course.name:
        flask.flash(
            "Course name is already in use.", "danger"
        )
        return flask.redirect("/courses")

    course.name = data.get("name")
    db.session.commit()

    flask.flash("Course updated successfully.", "success")

    return flask.redirect("/courses")
