import getpass
import secrets
import sys

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from extensions import register_extensions, db
from model import User
from views import register_views

app = Flask(__name__)
CORS(app)
migrate = Migrate(app, db)

app.config.from_pyfile("config.py")

register_extensions(app)
register_views(app)


@app.cli.command("createsuperuser", help="Used to create a superuser.")
def createsuperuser():
    data = {
        "name": input("Name: "),
        "email": input("Email: "),
        "password": getpass.getpass("Password: "),
        "password_confirmation": getpass.getpass("Password (again): "),
    }

    for field, value in data.items():
        if value is None:
            raise ValueError(f"{field}: This field is required.")

    if not secrets.compare_digest(
        data.get("password"), data.get("password_confirmation")
    ):
        raise ValueError("Passwords do not match.")

    try:
        user = User(
            name=data.get("name"),
            email=data.get("email"),
            role="administrator",
        )
        user.set_password(data.get("password"))

        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        print("Email address is already in use.")
        sys.exit(1)
    else:
        print("Superuser created successfully.")
