import os
import secrets

import flask
import flask_login
import werkzeug.utils

from extensions import db
from lib import request_input
from model import Course, Student, User

students_blueprint = flask.Blueprint("students", __name__)


@students_blueprint.get("/students", strict_slashes=False)
@flask_login.login_required
def list_():
    students = Student.query.all()
    return flask.render_template("students/index.html", students=students)


@students_blueprint.route(
    "/students/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
def create_student():
    if flask.request.method == "GET":
        courses = Course.query.all()
        return flask.render_template("students/create.html", courses=courses)

    data = {
        "course_id": request_input("course_id"),
        "name": request_input("name"),
        "email": request_input("email"),
        "password": request_input("password"),
        "password_confirmation": request_input("password_confirmation"),
        "image": flask.request.files["image"],
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

    filename = werkzeug.utils.secure_filename(data.get("image").filename)
    data.get("image").save(
        os.path.join(flask.current_app.config["UPLOAD_FOLDER"], filename),
    )

    user = User(
        name=data.get("name"),
        email=data.get("email"),
        role="student",
    )
    user.set_password(data.get("password"))

    course = Course.query.get_or_404(data.get("course_id"))
    student = Student(user=user, image_filename=filename, course=course)

    db.session.add_all([user, student])
    db.session.commit()

    flask.flash("Student has been added.", "success")

    return flask.redirect("/students")


@students_blueprint.route(
    "/students/<int:student_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False,
)
@flask_login.login_required
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
@flask_login.login_required
def update(student_id):
    student = Student.query.get_or_404(student_id)

    if flask.request.method == "GET":
        return flask.render_template("students/edit.html", student=student)

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

    if flask.request.files["image"]:
        filename = werkzeug.utils.secure_filename(data.get("image").filename)
        data.get("image").save(
            os.path.join(flask.current_app.config["UPLOAD_FOLDER"], filename),
        )

        student.user.image_filename = filename


    student.user.name = data.get("name")
    student.user.email = data.get("email")

    db.session.commit()

    flask.flash("Student updated successfully.", "success")

    return flask.redirect("/students")
