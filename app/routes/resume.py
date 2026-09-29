import os
import hashlib

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.utils import secure_filename

from app import db
from app.models.resume import Resume
from app.services.resume_parser import extract_resume_text

resume_bp = Blueprint("resume", __name__)

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@resume_bp.route("/upload-resume", methods=["GET", "POST"])
def upload_resume():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        if "resume" not in request.files:
            flash("No file selected.")
            return redirect(url_for("resume.upload_resume"))

        file = request.files["resume"]

        if file.filename == "":
            flash("No file selected.")
            return redirect(url_for("resume.upload_resume"))

        if not allowed_file(file.filename):
            flash("Only PDF and DOCX files are allowed.")
            return redirect(url_for("resume.upload_resume"))

        filename = secure_filename(file.filename)

        # Check if this user has already uploaded
        # a resume with the same filename
        existing_resume = Resume.query.filter_by(
            filename=filename,
            user_id=session["user_id"]
        ).first()

        if existing_resume:
            flash(
                "This resume has already been uploaded."
            )
            return redirect(
                url_for("resume.upload_resume")
            )

        # Calculate SHA-256 hash of the uploaded file
        file.seek(0)

        file_hash = hashlib.sha256(
            file.read()
        ).hexdigest()

        file.seek(0)

        # Check if the same file has already been uploaded
        existing_hash = Resume.query.filter_by(
            file_hash=file_hash,
            user_id=session["user_id"]
        ).first()

        if existing_hash:
            flash(
                "This resume has already been uploaded, even though the filename may be different."
            )
            return redirect(
                url_for("resume.upload_resume")
            )

        # Create upload directory
        upload_folder = os.path.join(
            os.getcwd(),
            "uploads",
            "resumes"
        )

        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(
            upload_folder,
            filename
        )

        # Save the uploaded file
        file.save(filepath)

        # Extract text from the resume
        try:
            extracted_text = extract_resume_text(filepath)

        except Exception as e:
            flash("Could not extract text from the resume.")
            return redirect(url_for("resume.upload_resume"))

        # Save information in database
        new_resume = Resume(
            filename=filename,
            filepath=filepath,
            file_hash=file_hash,
            extracted_text=extracted_text,
            user_id=session["user_id"]
        )

        db.session.add(new_resume)
        db.session.commit()

        flash("Resume uploaded and text extracted successfully!")
        return redirect(url_for("resume.upload_resume"))

    return render_template("upload_resume.html")