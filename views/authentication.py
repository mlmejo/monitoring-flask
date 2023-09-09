import flask
import flask_login

from model import User

authentication_blueprint = flask.Blueprint("authentication", __name__)


@authentication_blueprint.post("/login")
def login():
    user = User.filter_by_email(flask.request.form.get("email")).first()

    if user and user.check_password(flask.request.form.get("password")):
        flask_login.login_user(user)
        return flask.redirect("/subjects")

    flask.flash(
        "The provided credentials do not match our records.",
        "danger",
    )

    return flask.redirect("/")


@authentication_blueprint.post("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect("/")
