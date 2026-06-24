from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user
from models import db, User, Line, ScrapReason
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
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "HG" and password == "123":
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return """
    <h1>Scrap Tracker Dashboard</h1>
    <p>Login Successful</p>
    <a href='/add-scrap'>Add Scrap Record</a>
    """


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

    db.session.commit()


with app.app_context():
    db.create_all()
    seed_defaults()


if __name__ == "__main__":
    app.run(debug=True)
