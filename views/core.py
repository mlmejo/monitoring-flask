import flask
from sqlalchemy import func

from extensions import db
from model import Attendance

core_blueprint = flask.Blueprint("core", __name__)


@core_blueprint.route("/")
def welcome():
    return flask.redirect("/login")


@core_blueprint.route("/dashboard")
def dashboard():
    results = (
        db.session.query(
            func.extract('month', Attendance.time_in).label('month'),
            func.count().label('count')
        )
        .group_by(func.extract('month', Attendance.time_in))
        .order_by(func.extract('month', Attendance.time_in))
        .all()
    )
    chart_data = [{'month': result.month, 'count': result.count} for result in results]
    return flask.render_template("dashboard.html", chart_data=chart_data)
