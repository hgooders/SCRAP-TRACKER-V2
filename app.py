from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    send_file
)
from collections import counter

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models import (
    db,
    User,
    Line,
    ScrapReason,
    ScrapRecord
)

from datetime import datetime, timedelta
from io import BytesIO
from openpyxl import Workbook

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


# ------------------------
# DEFAULT DATA
# ------------------------

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

        if not Line.query.filter_by(
            name=line
        ).first():

            db.session.add(
                Line(name=line)
            )

    for reason in reasons:

        if not ScrapReason.query.filter_by(
            name=reason
        ).first():

            db.session.add(
                ScrapReason(name=reason)
            )

    if not User.query.filter_by(
        username="admin"
    ).first():

        admin = User(
            username="admin",
            password_hash=generate_password_hash(
                "admin123"
            ),
            role="admin"
        )

        db.session.add(admin)

    db.session.commit()


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    return redirect(
        url_for("login")
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password_hash,
            password
        ):

            login_user(user)

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password"
        )

    return render_template(
        "login.html"
    )


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


@app.route("/dashboard")
@login_required
def dashboard():

    all_records = ScrapRecord.query.all()

    today = datetime.utcnow().date()

    today_qty = sum(
        r.quantity
        for r in all_records
        if r.created_at.date() == today
    )

    week_qty = sum(
        r.quantity
        for r in all_records
        if (
            today - r.created_at.date()
        ).days <= 7
    )

    month_qty = sum(
        r.quantity
        for r in all_records
        if r.created_at.month == today.month
        and r.created_at.year == today.year
    )

    total_qty = sum(
        r.quantity
        for r in all_records
    )

    records = ScrapRecord.query.order_by(
        ScrapRecord.created_at.desc()
    ).limit(25).all()

    # Scrap by Reason
reason_counter = Counter()

for r in all_records:
    reason_counter[r.reason] += r.quantity

reason_labels = list(reason_counter.keys())
reason_values = list(reason_counter.values())

# Scrap by Origin Line
line_counter = Counter()

for r in all_records:
    line_counter[r.origin_line] += r.quantity

line_labels = list(line_counter.keys())
line_values = list(line_counter.values())
    
    return render_template(
        "dashboard.html",
       records=records,
today_qty=today_qty,
week_qty=week_qty,
month_qty=month_qty,
total_qty=total_qty,

reason_labels=reason_labels,
reason_values=reason_values,

line_labels=line_labels,
line_values=line_values

    )

    
@app.route("/add-scrap", methods=["GET", "POST"])
@login_required
def add_scrap():

    lines = Line.query.order_by(
        Line.name
    ).all()

    reasons = ScrapReason.query.order_by(
        ScrapReason.name
    ).all()

    if request.method == "POST":

        record = ScrapRecord(
            part_number=request.form[
                "part_number"
            ],

            part_name=request.form[
                "part_name"
            ],

            quantity=int(
                request.form["quantity"]
            ),

            reason=request.form[
                "reason"
            ],

            other_reason=request.form.get(
                "other_reason"
            ),

            origin_line=request.form[
                "origin_line"
            ],

            destination_line=request.form[
                "destination_line"
            ],

            comments=request.form.get(
                "comments"
            ),

            submitted_by=current_user.username
        )

        db.session.add(record)
        db.session.commit()

        flash(
            "Scrap record added successfully"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "add_scrap.html",
        lines=lines,
        reasons=reasons
    )


@app.route("/reports")
@login_required
def reports():

    records = ScrapRecord.query.order_by(
        ScrapRecord.created_at.desc()
    ).all()

    return render_template(
        "reports.html",
        records=records
    )


@app.route("/export-excel")
@login_required
def export_excel():

    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Scrap Records"

    headers = [
        "Date",
        "Part Number",
        "Part Name",
        "Quantity",
        "Reason",
        "Other Reason",
        "Origin Line",
        "Destination Line",
        "Comments",
        "Submitted By"
    ]

    sheet.append(headers)

    records = ScrapRecord.query.order_by(
        ScrapRecord.created_at.desc()
    ).all()

    for record in records:

        sheet.append([
            record.created_at.strftime(
                "%d/%m/%Y %H:%M"
            ),

            record.part_number,
            record.part_name,
            record.quantity,
            record.reason,
            record.other_reason,
            record.origin_line,
            record.destination_line,
            record.comments,
            record.submitted_by
        ])

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="Scrap_Report.xlsx",
        mimetype=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

@app.route("/delete-record/<int:record_id>", methods=["POST"])

@login_required

def delete_record(record_id):



    record = ScrapRecord.query.get_or_404(

        record_id

    )



    db.session.delete(record)



    db.session.commit()



    flash(

        "Scrap record deleted successfully."

    )



    return redirect(

        url_for("reports")

    )

# ------------------------
# STARTUP
# ------------------------

with app.app_context():

    db.create_all()

    seed_defaults()


if __name__ == "__main__":
    app.run(debug=True)
