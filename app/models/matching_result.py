from app import db
from datetime import datetime


class MatchingResult(db.Model):

    __tablename__ = "matching_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    resume_id = db.Column(
        db.Integer,
        db.ForeignKey("resumes.id"),
        nullable=False
    )

    job_description_id = db.Column(
        db.Integer,
        db.ForeignKey("job_descriptions.id"),
        nullable=False
    )

    tfidf_score = db.Column(
        db.Float,
        nullable=False
    )

    semantic_score = db.Column(
        db.Float,
        nullable=False
    )

    skills_score = db.Column(
        db.Float,
        nullable=False
    )

    experience_score = db.Column(
        db.Float,
        nullable=False
    )

    education_score = db.Column(
        db.Float,
        nullable=False
    )

    final_score = db.Column(
        db.Float,
        nullable=False
    )

    candidate_classification = db.Column(
        db.String(100),
        nullable=True
    )

    hr_recommendation = db.Column(
        db.Text,
        nullable=True
    )

    plagiarism_score = db.Column(
        db.Float,
        nullable=True
    )

    plagiarism_classification = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    resume = db.relationship(
        "Resume",
        backref=db.backref(
            "matching_results",
            lazy=True
        )
    )

    job_description = db.relationship(
        "JobDescription",
        backref=db.backref(
            "matching_results",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<MatchingResult {self.id}>"