from app import db
from datetime import datetime


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(255), nullable=False)

    filepath = db.Column(db.String(500), nullable=False)

    file_hash = db.Column(
    db.String(64),
    nullable=True
    )

    extracted_text = db.Column(db.Text, nullable=True)

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
        backref=db.backref("resumes", lazy=True)
    )

    def __repr__(self):
        return f"<Resume {self.filename}>"