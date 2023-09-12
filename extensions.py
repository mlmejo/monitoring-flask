from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()

login_manager.login_view = "core.welcome"


def register_extensions(app):
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
