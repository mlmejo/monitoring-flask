import flask

from extensions import db
from lib import request_input
from model import Subject

subjects_blueprint = flask.Blueprint("subjects", __name__)


@subjects_blueprint.get("/subjects", strict_slashes=False)
def list_():
    subjects = Subject.query.all()
    return flask.render_template("subjects/index.html", subjects=subjects)


@subjects_blueprint.route(
    "/subjects/create",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def create_subject():
    if flask.request.method == "GET":
        return flask.render_template("subjects/create.html")

    data = {
        "title": request_input("title"),
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: The field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/subjects")

    exists = Subject.query.filter_by(title=data.get("title")).first()

    if exists:
        flask.flash("Subject with title already exists.", "danger")
        return flask.redirect("/subjects")

    subject = Subject(**data)
    db.session.add(subject)
    db.session.commit()

    flask.flash("Subject has been created.", "success")

    return flask.redirect("/subjects")


@subjects_blueprint.route(
    "/subjects/<int:subject_id>/delete",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def subject_delete(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if flask.request.method == "POST":
        flask.flash(f"{subject.title} deleted successfully.", "success")

        db.session.delete(subject)
        db.session.commit()

        return flask.redirect("/subjects")

    return flask.render_template("subjects/delete.html", subject=subject)


@subjects_blueprint.route(
    "/subjects/<int:subject_id>/edit",
    methods=["GET", "POST"],
    strict_slashes=False,
)
def update(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if flask.request.method == "GET":
        return flask.render_template("subjects/edit.html", subject=subject)

    data = {
        "title": request_input("title"),
    }

    error = False
    for field, value in data.items():
        if value is not None:
            continue
        flask.flash(f"{field}: This field is required.", "danger")
        error = True

    if error:
        return flask.redirect("/subjects")

    exists = Subject.query.filter_by(title=data.get("title")).first()

    if exists and not exists.title == subject.title:
        flask.flash(
            "Another subject with these details already exists.",
            "danger",
        )
        return flask.redirect("/subjects")

    subject.title = data.get("title")
    db.session.commit()

    flask.flash(f"Subject updated successfully.", "success")

    return flask.redirect("/subjects")