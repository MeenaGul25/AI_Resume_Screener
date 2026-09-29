import csv
from io import StringIO
from flask import Response
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.matching_result import MatchingResult
from app import db

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


@admin_bp.route("/dashboard")
def dashboard():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Get current user
    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can access this page
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    total_users = User.query.count()

    total_resumes = Resume.query.count()

    total_job_descriptions = JobDescription.query.count()

    total_matches = MatchingResult.query.count()

    total_plagiarism_checks = MatchingResult.query.filter(
        MatchingResult.plagiarism_score.isnot(None)
    ).count()

    plagiarism_scores = MatchingResult.query.filter(
        MatchingResult.plagiarism_score.isnot(None)
    ).all()

    if plagiarism_scores:
        average_plagiarism_score = sum(
            result.plagiarism_score
            for result in plagiarism_scores
        ) / len(plagiarism_scores)
    else:
        average_plagiarism_score = 0

    average_score = db.session.query(
        db.func.avg(MatchingResult.final_score)
    ).scalar()

    highest_score = db.session.query(
        db.func.max(MatchingResult.final_score)
    ).scalar()

    latest_match = MatchingResult.query.order_by(
        MatchingResult.created_at.desc()
    ).first()

    recent_matches = MatchingResult.query.order_by(
        MatchingResult.created_at.desc()
    ).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_resumes=total_resumes,
        total_job_descriptions=total_job_descriptions,
        total_matches=total_matches,
        total_plagiarism_checks=total_plagiarism_checks,
        average_plagiarism_score=average_plagiarism_score,
        average_score=average_score,
        highest_score=highest_score,
        latest_match=latest_match,
        recent_matches=recent_matches
    )


@admin_bp.route("/users")
def users():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can access this page
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    search = request.args.get("search", "").strip()

    if search:
        users = User.query.filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        ).all()
    else:
        users = User.query.all()

    return render_template(
        "admin_users.html",
        users=users,
        search=search
    )

@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can delete users
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    user = User.query.get(user_id)

    if not user:
        flash("User not found.")
        return redirect(
            url_for("admin.users")
        )

    # Prevent admin from deleting their own account
    if user.id == current_user.id:
        flash("You cannot delete your own admin account.")
        return redirect(
            url_for("admin.users")
        )

    db.session.delete(user)
    db.session.commit()

    flash(
        f"User {user.name} deleted successfully."
    )

    return redirect(
        url_for("admin.users")
    )

@admin_bp.route(
    "/users/change-role/<int:user_id>",
    methods=["POST"]
)
def change_user_role(user_id):

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can change roles
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    user = User.query.get(user_id)

    if not user:
        flash("User not found.")
        return redirect(
            url_for("admin.users")
        )

    # Prevent admin from changing their own role
    if user.id == current_user.id:
        flash("You cannot change your own admin role.")
        return redirect(
            url_for("admin.users")
        )

    new_role = request.form.get("role")

    if new_role not in ["HR", "ADMIN"]:
        flash("Invalid role selected.")
        return redirect(
            url_for("admin.users")
        )

    user.role = new_role

    db.session.commit()

    flash(
        f"{user.name}'s role changed to {new_role}."
    )

    return redirect(
        url_for("admin.users")
    )


@admin_bp.route("/resumes/view/<int:resume_id>")
def view_resume(resume_id):

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can access this page
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    resume = Resume.query.get(resume_id)

    if not resume:
        flash("Resume not found.")
        return redirect(
            url_for("admin.resumes")
        )

    return render_template(
        "admin_resume_detail.html",
        resume=resume
    )

@admin_bp.route("/job-descriptions/view/<int:job_id>")
def view_job_description(job_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_user = User.query.get(session["user_id"])

    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(url_for("main.dashboard"))

    job = JobDescription.query.get(job_id)

    if not job:
        flash("Job description not found.")
        return redirect(url_for("admin.job_descriptions"))

    return render_template(
        "admin_job_description_detail.html",
        job=job
    )

@admin_bp.route("/resumes")
def resumes():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can access this page
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    search = request.args.get("search", "").strip()

    if search:
        resumes = Resume.query.filter(
            Resume.filename.ilike(f"%{search}%")
        ).all()
    else:
        resumes = Resume.query.all()

    return render_template(
        "admin_resumes.html",
        resumes=resumes,
        search=search
    )

@admin_bp.route("/job-descriptions")
def job_descriptions():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    current_user = User.query.get(
        session["user_id"]
    )

    # Only ADMIN can access this page
    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(
            url_for("main.dashboard")
        )

    search = request.args.get("search", "").strip()

    if search:
        job_descriptions = JobDescription.query.filter(
            JobDescription.title.ilike(f"%{search}%")
        ).all()
    else:
        job_descriptions = JobDescription.query.all()

    return render_template(
        "admin_job_descriptions.html",
        job_descriptions=job_descriptions,
        search=search
    )


@admin_bp.route("/matching-results")
def matching_results():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_user = User.query.get(session["user_id"])

    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(url_for("main.dashboard"))

    # Get filters
    classification = request.args.get(
        "classification",
        ""
    ).strip()

    plagiarism_status = request.args.get(
        "plagiarism_status",
        ""
    ).strip()

    score_range = request.args.get(
        "score_range",
        ""
    ).strip()

    # Get sorting option
    sort_by = request.args.get(
        "sort_by",
        "newest"
    ).strip()

    # Build query
    query = MatchingResult.query

    # Candidate classification filter
    if classification:
        query = query.filter(
            MatchingResult.candidate_classification
            == classification
        )

    # Plagiarism status filter
    if plagiarism_status:
        query = query.filter(
            MatchingResult.plagiarism_classification
            == plagiarism_status
        )

    # Final score filter
    if score_range == "80-100":

        query = query.filter(
            MatchingResult.final_score >= 80,
            MatchingResult.final_score <= 100
        )

    elif score_range == "60-79":

        query = query.filter(
            MatchingResult.final_score >= 60,
            MatchingResult.final_score < 80
        )

    elif score_range == "40-59":

        query = query.filter(
            MatchingResult.final_score >= 40,
            MatchingResult.final_score < 60
        )

    elif score_range == "0-39":

        query = query.filter(
            MatchingResult.final_score >= 0,
            MatchingResult.final_score < 40
        )

    # Sorting
    if sort_by == "oldest":

        query = query.order_by(
            MatchingResult.created_at.asc()
        )

    elif sort_by == "highest_score":

        query = query.order_by(
            MatchingResult.final_score.desc()
        )

    elif sort_by == "lowest_score":

        query = query.order_by(
            MatchingResult.final_score.asc()
        )

    else:

        # Default: newest first
        query = query.order_by(
            MatchingResult.created_at.desc()
        )

    # Get ALL filtered results
    # Used for the summary statistics
    all_results = query.all()

    # Current page number
    page = request.args.get(
        "page",
        1,
        type=int
    )

    # Pagination
    pagination = query.paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    # Results displayed on current page
    results = pagination.items

    # Summary statistics
    total_results = len(all_results)

    if total_results > 0:

        average_score = sum(
            result.final_score
            for result in all_results
        ) / total_results

        highest_score = max(
            result.final_score
            for result in all_results
        )

        lowest_score = min(
            result.final_score
            for result in all_results
        )

    else:

        average_score = 0
        highest_score = 0
        lowest_score = 0

    plagiarism_results = [
        result for result in all_results
        if result.plagiarism_score is not None
    ]

    total_plagiarism_checks = len(plagiarism_results)

    if plagiarism_results:

        average_plagiarism_score = sum(
            result.plagiarism_score
            for result in plagiarism_results
        ) / total_plagiarism_checks

        highest_plagiarism_score = max(
            result.plagiarism_score
            for result in plagiarism_results
        )

        lowest_plagiarism_score = min(
            result.plagiarism_score
            for result in plagiarism_results
        )

    else:

        average_plagiarism_score = 0
        highest_plagiarism_score = 0
        lowest_plagiarism_score = 0


    strong_candidates = sum(
        1 for result in all_results
        if result.candidate_classification == "Strong Candidate"
    )

    good_candidates = sum(
        1 for result in all_results
        if result.candidate_classification == "Good Candidate"
    )

    moderate_candidates = sum(
        1 for result in all_results
        if result.candidate_classification == "Moderate Candidate"
    )

    weak_candidates = sum(
        1 for result in all_results
        if result.candidate_classification == "Weak Candidate"
    )

    if total_results > 0:

        strong_percentage = (
            strong_candidates / total_results
        ) * 100

        good_percentage = (
            good_candidates / total_results
        ) * 100

        moderate_percentage = (
            moderate_candidates / total_results
        ) * 100

        weak_percentage = (
            weak_candidates / total_results
        ) * 100

    else:

        strong_percentage = 0
        good_percentage = 0
        moderate_percentage = 0
        weak_percentage = 0

    low_similarity = sum(
        1 for result in all_results
        if result.plagiarism_classification == "Low Similarity"
    )

    moderate_similarity = sum(
        1 for result in all_results
        if result.plagiarism_classification == "Moderate Similarity"
    )

    high_similarity = sum(
        1 for result in all_results
        if result.plagiarism_classification == "High Similarity"
    )

    very_high_similarity = sum(
        1 for result in all_results
        if result.plagiarism_classification == "Very High Similarity"
    )

    last_updated = datetime.now()

    return render_template(
        "admin_matching_results.html",

        results=results,

        classification=classification,

        plagiarism_status=plagiarism_status,

        score_range=score_range,

        sort_by=sort_by,

        total_results=total_results,

        average_score=average_score,

        highest_score=highest_score,

        lowest_score=lowest_score,

        total_plagiarism_checks=total_plagiarism_checks,

        average_plagiarism_score=average_plagiarism_score,

        highest_plagiarism_score=highest_plagiarism_score,

        lowest_plagiarism_score=lowest_plagiarism_score,

        pagination=pagination,

        strong_candidates=strong_candidates,

        good_candidates=good_candidates,

        moderate_candidates=moderate_candidates,

        weak_candidates=weak_candidates,

        strong_percentage=strong_percentage,

        good_percentage=good_percentage,

        moderate_percentage=moderate_percentage,

        weak_percentage=weak_percentage,

        low_similarity=low_similarity,

        moderate_similarity=moderate_similarity,

        high_similarity=high_similarity,

        very_high_similarity=very_high_similarity,

        last_updated=last_updated
    )

@admin_bp.route("/matching-results/export")
def export_matching_results():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_user = User.query.get(session["user_id"])

    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(url_for("main.dashboard"))

    # Get filters
    classification = request.args.get(
        "classification",
        ""
    ).strip()

    plagiarism_status = request.args.get(
        "plagiarism_status",
        ""
    ).strip()

    score_range = request.args.get(
        "score_range",
        ""
    ).strip()

    # Get sorting option
    sort_by = request.args.get(
        "sort_by",
        "newest"
    ).strip()

    # Build query
    query = MatchingResult.query

    # Candidate classification filter
    if classification:
        query = query.filter(
            MatchingResult.candidate_classification
            == classification
        )

    # Plagiarism status filter
    if plagiarism_status:
        query = query.filter(
            MatchingResult.plagiarism_classification
            == plagiarism_status
        )

    # Final score filter
    if score_range == "80-100":

        query = query.filter(
            MatchingResult.final_score >= 80,
            MatchingResult.final_score <= 100
        )

    elif score_range == "60-79":

        query = query.filter(
            MatchingResult.final_score >= 60,
            MatchingResult.final_score < 80
        )

    elif score_range == "40-59":

        query = query.filter(
            MatchingResult.final_score >= 40,
            MatchingResult.final_score < 60
        )

    elif score_range == "0-39":

        query = query.filter(
            MatchingResult.final_score >= 0,
            MatchingResult.final_score < 40
        )

    # Sorting
    if sort_by == "oldest":

        query = query.order_by(
            MatchingResult.created_at.asc()
        )

    elif sort_by == "highest_score":

        query = query.order_by(
            MatchingResult.final_score.desc()
        )

    elif sort_by == "lowest_score":

        query = query.order_by(
            MatchingResult.final_score.asc()
        )

    else:

        query = query.order_by(
            MatchingResult.created_at.desc()
        )

    results = query.all()

    # Create CSV
    output = StringIO()

    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "ID",
        "Resume",
        "Job Description",
        "TF-IDF Score",
        "Semantic Score",
        "Skills Score",
        "Experience Score",
        "Education Score",
        "Final Score",
        "Candidate Classification",
        "Plagiarism Score",
        "Plagiarism Status",
        "HR Recommendation",
        "Date"
    ])

    # CSV rows
    for result in results:

        writer.writerow([
            result.id,

            result.resume.filename
            if result.resume else "N/A",

            result.job_description.title
            if result.job_description else "N/A",

            result.tfidf_score,

            result.semantic_score,

            result.skills_score,

            result.experience_score,

            result.education_score,

            result.final_score,

            result.candidate_classification
            if result.candidate_classification
            else "N/A",

            result.plagiarism_score
            if result.plagiarism_score is not None
            else "N/A",

            result.plagiarism_classification
            if result.plagiarism_classification
            else "N/A",

            result.hr_recommendation
            if result.hr_recommendation
            else "N/A",

            result.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if result.created_at
            else "N/A"
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=matching_history.csv"
    )

    return response

@admin_bp.route("/matching-results/view/<int:result_id>")
def view_matching_result(result_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_user = User.query.get(session["user_id"])

    if not current_user or current_user.role != "ADMIN":
        flash("Access denied. Admins only.")
        return redirect(url_for("main.dashboard"))

    result = MatchingResult.query.get(result_id)

    if not result:
        flash("Matching result not found.")
        return redirect(url_for("admin.matching_results"))

    return render_template(
        "admin_matching_result_detail.html",
        result=result
    )