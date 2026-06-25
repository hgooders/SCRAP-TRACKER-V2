from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="operator")


class Line(db.Model):
    __tablename__ = "lines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class ScrapReason(db.Model):
    __tablename__ = "scrap_reasons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class ScrapRecord(db.Model):
    __tablename__ = "scrap_records"

    id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    part_number = db.Column(db.String(100), nullable=False)
    part_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.String(100), nullable=False)
    other_reason = db.Column(db.String(255))

    origin_line = db.Column(db.String(100), nullable=False)
    destination_line = db.Column(db.String(100), nullable=False)

    comments = db.Column(db.Text)
    submitted_by = db.Column(db.String(100))

    photos = db.relationship(
        "ScrapPhoto",
        backref="scrap_record",
        lazy=True,
        cascade="all, delete-orphan"
    )


class ScrapPhoto(db.Model):
    __tablename__ = "scrap_photos"

    id = db.Column(db.Integer, primary_key=True)

    scrap_record_id = db.Column(
        db.Integer,
        db.ForeignKey("scrap_records.id"),
        nullable=False
    )

    filename = db.Column(db.String(255), nullable=False)

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
