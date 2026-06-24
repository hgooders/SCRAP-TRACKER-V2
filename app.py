from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Line, ScrapReason, ScrapRecord
import os

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///scrap_tracker.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))
  def seed_defaults():
    lines = [
        "Trim 1",
        "Trim 2 / IP",
        "Chassis 1",
        "Chassis 2",
        "Chassis 3",
        "Engine Line",
        "Door Line",
        "Final 1",
        "Final 2"
    ]

    reasons = [
        "Damage",
        "Cross Thread",
        "Spinning Bolt/Nut",
        "Snapped Tab",
        "Tuck",
        "Deformity",
        "Other"
    ]

    for line in lines:
        if not Line.query.filter_by(name=line).first():
            db.session.add(Line(name=line))

    for reason in reasons:
        if not ScrapReason.query.filter_by(name=reason).first():
            db.session.add(ScrapReason(name=reason))

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)

    db.session.commit()

with app.app_context():
    db.create_all()
    seed_defaults()
