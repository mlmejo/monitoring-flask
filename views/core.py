import flask
import flask_login
from sqlalchemy import func

from extensions import db
from model import Attendance, Teacher, Student

core_blueprint = flask.Blueprint("core", __name__)


@core_blueprint.route("/")
def welcome():
    return flask.redirect("/login")


@core_blueprint.route("/dashboard")
@flask_login.login_required
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
    template = 'dashboard.html'
    model = None

    if flask_login.current_user.role == 'teacher':
        template = 'teacher_dashboard.html'
        model = Teacher.query.filter_by(user_id=flask_login.current_user.id).first()

    elif flask_login.current_user.role == 'student':
        template = 'student_dashboard.html'
        model = Student.query.filter_by(user_id=flask_login.current_user.id).first()

    return flask.render_template(template, chart_data=chart_data, model=model)
