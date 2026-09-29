from flask import Blueprint, render_template, session, redirect, url_for

from app import db
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.matching_result import MatchingResult


main = Blueprint("main", __name__)

@main.route("/")
def landing_page():
    return render_template("landing.html")

@main.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Count resumes uploaded by the logged-in HR
    resume_count = Resume.query.filter_by(
        user_id=user_id
    ).count()

    # Count job descriptions uploaded by the logged-in HR
    job_description_count = JobDescription.query.filter_by(
        user_id=user_id
    ).count()

    # Count matching results belonging to the logged-in HR
    matching_count = (
        MatchingResult.query
        .join(Resume, MatchingResult.resume_id == Resume.id)
        .filter(Resume.user_id == user_id)
        .count()
    )

    return render_template(
        "dashboard.html",
        user_name=session["user_name"],
        user_role=session["user_role"],
        resume_count=resume_count,
        job_description_count=job_description_count,
        matching_count=matching_count
    )