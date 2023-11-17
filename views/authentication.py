import flask
import flask_login

from model import User

authentication_blueprint = flask.Blueprint("authentication", __name__)


@authentication_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "GET":
        return flask.render_template("welcome.html")

    user = User.filter_by_email(flask.request.form.get("email")).first()

    if user and user.check_password(flask.request.form.get("password")):
        flask_login.login_user(user)
        next_page = flask.request.args.get("next")

        print(next_page)

        if next_page:
            return flask.redirect(next_page)
        else:
            return flask.redirect("/dashboard")

    flask.flash(
        "The provided credentials do not match our records.",
        "danger",
    )

    return flask.redirect("/")


@authentication_blueprint.post("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect("/")
