import sqlite3
import calendar
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from database.db import init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # TODO: load from env var in production

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm  = request.form.get("confirm_password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")
    if password != confirm:
        return render_template("register.html", error="Passwords do not match.")

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.")

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="All fields are required.")

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 4"


def _parse_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


def _resolve_period(period: str) -> Tuple[Optional[str], Optional[str]]:
    today = date.today()
    if period == "this_month":
        from_d = today.replace(day=1).isoformat()
        last_day = calendar.monthrange(today.year, today.month)[1]
        to_d = today.replace(day=last_day).isoformat()
        return from_d, to_d
    if period == "last_month":
        last_month_end = today.replace(day=1) - timedelta(days=1)
        from_d = last_month_end.replace(day=1).isoformat()
        to_d = last_month_end.isoformat()
        return from_d, to_d
    if period == "last_3_months":
        # Subtract 3 months manually; adjust year if we cross a January boundary
        month = today.month - 3
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        from_d = date(year, month, 1).isoformat()
        to_d = today.isoformat()
        return from_d, to_d
    return None, None


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    uid = session["user_id"]

    from_date = _parse_date(request.args.get("from_date"))
    to_date   = _parse_date(request.args.get("to_date"))
    period    = request.args.get("period", "")
    active_period = None

    if from_date is None and to_date is None and period:
        from_date, to_date = _resolve_period(period)
        if from_date:
            active_period = period

    limit = None if (from_date or to_date) else 10
    custom_date_filter = bool((from_date or to_date) and not active_period)

    user      = get_user_by_id(uid)
    stats     = get_summary_stats(uid, from_date=from_date, to_date=to_date)
    recent    = get_recent_transactions(uid, limit=limit,
                                        from_date=from_date, to_date=to_date)
    breakdown = get_category_breakdown(uid, from_date=from_date, to_date=to_date)
    return render_template("profile.html",
                           user=user, stats=stats,
                           recent=recent, breakdown=breakdown,
                           from_date=from_date, to_date=to_date,
                           active_period=active_period,
                           custom_date_filter=custom_date_filter)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    import os
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5001)
