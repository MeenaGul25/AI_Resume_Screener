import os

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
from app.models.job_description import JobDescription
from app.services.resume_parser import extract_resume_text


job_bp = Blueprint(
    "job",
    __name__
)


ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


@job_bp.route(
    "/upload-job-description",
    methods=["GET", "POST"]
)
def upload_job_description():

    # Make sure HR is logged in
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title"
        )

        if not title:
            flash(
                "Please enter a job title."
            )

            return redirect(
                url_for(
                    "job.upload_job_description"
                )
            )

        if "job_description" not in request.files:

            flash(
                "No file selected."
            )

            return redirect(
                url_for(
                    "job.upload_job_description"
                )
            )

        file = request.files[
            "job_description"
        ]

        if file.filename == "":

            flash(
                "No file selected."
            )

            return redirect(
                url_for(
                    "job.upload_job_description"
                )
            )

        if not allowed_file(
            file.filename
        ):

            flash(
                "Only PDF and DOCX files are allowed."
            )

            return redirect(
                url_for(
                    "job.upload_job_description"
                )
            )

        filename = secure_filename(
            file.filename
        )

        upload_folder = os.path.join(
            os.getcwd(),
            "uploads",
            "job_descriptions"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        filepath = os.path.join(
            upload_folder,
            filename
        )

        # Save the file
        file.save(filepath)

        # Extract text
        try:

            extracted_text = extract_resume_text(
                filepath
            )

        except Exception:

            flash(
                "Could not extract text from the job description."
            )

            return redirect(
                url_for(
                    "job.upload_job_description"
                )
            )

        # Create database record
        new_job = JobDescription(

            title=title,

            filename=filename,

            filepath=filepath,

            extracted_text=extracted_text,

            user_id=session[
                "user_id"
            ]
        )

        db.session.add(
            new_job
        )

        db.session.commit()

        flash(
            "Job description uploaded and text extracted successfully!"
        )

        return redirect(
            url_for(
                "job.upload_job_description"
            )
        )

    return render_template(
        "upload_job_description.html"
    )