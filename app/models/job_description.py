from app import db
from datetime import datetime


class JobDescription(db.Model):
    __tablename__ = "job_descriptions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    filepath = db.Column(
        db.String(500),
        nullable=False
    )

    extracted_text = db.Column(
        db.Text,
        nullable=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "job_descriptions",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<JobDescription {self.title}>"