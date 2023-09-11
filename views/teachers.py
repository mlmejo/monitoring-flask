import secrets

import flask
import flask_login

from extensions import db
from lib import request_input
from model import Teacher, User

teachers_blueprint = flask.Blueprint("teachers", __name__)


@teachers_blueprint.get("/teachers", strict_slashes=False)
@flask_login.login_required
def list_():
    teachers = Teacher.query.all()
    return flask.render_template("teachers/index.html", teachers=teachers)


@teachers_blueprint.route(
    "/teachers/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def create_teacher():
    if flask.request.method == "GET":
        return flask.render_template("teachers/create.html")

    data = {
        "name": request_input("name"),
        "email": request_input("email"),
        "password": request_input("password"),
        "password_confirmation": request_input("password_confirmation"),
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: The field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/teachers")

    if not secrets.compare_digest(
        data.get("password"),
        data.get("password_confirmation"),
    ):
        flask.flash(
            "Passwords do not match",
            "danger",
        )
        return flask.redirect("/teachers")

    exists = User.query.filter_by(email=data.get("email")).first()

    if exists:
        flask.flash("Email address is already in use.", "danger")
        return flask.redirect("/teachers")

    user = User(
        name=data.get("name"),
        email=data.get("email"),
        role="teacher",
    )
    user.set_password(data.get("password"))

    teacher = Teacher(user=user)

    db.session.add_all([user, teacher])
    db.session.commit()

    flask.flash("Teacher has been added.", "success")

    return flask.redirect("/teachers")


@teachers_blueprint.route(
    "/teachers/<int:teacher_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def teacher_delete(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)

    if flask.request.method == "POST":
        flask.flash(f"{teacher.user.name} deleted successfully.", "success")

        db.session.delete(teacher)
        db.session.commit()

        return flask.redirect("/teachers")

    return flask.render_template("teachers/delete.html", teacher=teacher)


@teachers_blueprint.route(
    "/teachers/<int:teacher_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def update(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)

    if flask.request.method == "GET":
        return flask.render_template("teachers/edit.html", teacher=teacher)

    data = {
        "name": request_input("name"),
        "email": request_input("email"),
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: This field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/teachers")

    exists = User.query.filter_by(email=data.get("email")).first()

    if exists and not exists.email == teacher.user.email:
        flask.flash("Email is already in use.", "danger")
        return flask.redirect("/teachers")

    teacher.user.name = data.get("name")
    teacher.user.email = data.get("email")

    db.session.commit()

    flask.flash("Teacher updated successfully.", "success")

    return flask.redirect("/teachers")
