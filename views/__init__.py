from flask import Flask

from views.authentication import authentication_blueprint
from views.core import core_blueprint
from views.schedules import schedules_blueprint
from views.students import students_blueprint
from views.subjects import subjects_blueprint
from views.teachers import teachers_blueprint


def register_views(app: Flask):
    app.register_blueprint(authentication_blueprint)
    app.register_blueprint(core_blueprint)
    app.register_blueprint(schedules_blueprint)
    app.register_blueprint(students_blueprint)
    app.register_blueprint(subjects_blueprint)
    app.register_blueprint(teachers_blueprint)
