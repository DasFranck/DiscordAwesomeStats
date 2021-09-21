from flask import Flask

from .frontend import frontend
from .db import close_db

def create_app():
    app = Flask(__name__)
    app.register_blueprint(frontend)
    app.teardown_appcontext(close_db)
    return app
