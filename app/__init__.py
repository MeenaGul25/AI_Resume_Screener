import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///resume_screener.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Use environment variable in deployment.
    # Fall back to a development key when running locally.
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "development-secret-key"
    )

    db.init_app(app)

    from app.models.user import User
    from app.models.resume import Resume
    from app.models.job_description import JobDescription
    from app.models.matching_result import MatchingResult

    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.resume import resume_bp
    from app.routes.job_description import job_bp
    from app.routes.matching import matching_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app