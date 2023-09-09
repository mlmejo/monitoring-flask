import secrets

import flask

from extensions import db
from lib import request_input
from model import Student, User

students_blueprint = flask.Blueprint("students", __name__)


@students_blueprint.get("/students", strict_slashes=False)
def list_():
    students = Student.query.all()
    return flask.render_template("students/index.html", students=students)


@students_blueprint.route(
    "/students/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def create_student():
    if flask.request.method == "GET":
        return flask.render_template("students/create.html")

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
        return flask.redirect("/students")

    if not secrets.compare_digest(
        data.get("password"),
        data.get("password_confirmation"),
    ):
        flask.flash(
            "Passwords do not match",
            "danger",
        )
        return flask.redirect("/students")

    exists = User.query.filter_by(email=data.get("email")).first()

    if exists:
        flask.flash("Email address is already in use.", "danger")
        return flask.redirect("/students")

    user = User(name=data.get("name"), email=data.get("email"))
    user.set_password(data.get("password"))

    student = Student(user=user)

    db.session.add_all([user, student])
    db.session.commit()

    flask.flash("Student has been added.", "success")

    return flask.redirect("/students")


@students_blueprint.route(
    "/students/<int:student_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def student_delete(student_id):
    student = Student.query.get_or_404(student_id)

    if flask.request.method == "POST":
        flask.flash(f"{student.user.name} deleted successfully", "success")

        db.session.delete(student)
        db.session.commit()

        return flask.redirect("/students")

    return flask.render_template("students/delete.html", student=student)


@students_blueprint.route(
    "/students/<int:student_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=True,
)
def update(student_id):
    student = Student.query.get_or_404(student_id)

    if flask.request.method == "GET":
        return flask.render_template("students/edit.html")

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
        return flask.redirect("/students")

    exists = User.query.filter_by(email=data.get("email")).first()

    if exists and not exists.user.email == student.user.email:
        flask.flash("Email is already in use.", "danger")
        return flask.redirect("/students")

    student.user.name = data.get("name")
    student.user.email = data.get("email")

    db.session.commit()

    flask.flash("Student updated successfully.", "success")

    return flask.redirect("/students")
