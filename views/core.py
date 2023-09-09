import flask

core_blueprint = flask.Blueprint("core", __name__)


@core_blueprint.route("/")
def welcome():
    return flask.render_template("welcome.html")
