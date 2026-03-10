from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from openpyxl import Workbook

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pointage.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS presences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            arrival_time TEXT,
            departure_time TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    user_count = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if user_count == 0:
        db.execute(
            "INSERT INTO users (name, password, is_admin) VALUES (?, ?, ?)",
            ("admin", "admin123", 1),
        )
        db.execute(
            "INSERT INTO users (name, password, is_admin) VALUES (?, ?, ?)",
            ("alice", "alice123", 0),
        )
        db.execute(
            "INSERT INTO users (name, password, is_admin) VALUES (?, ?, ?)",
            ("bob", "bob123", 0),
        )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("is_admin"):
            flash("Accès réservé aux administrateurs.")
            return redirect(url_for("index"))
        return view(**kwargs)

    return wrapped_view


@app.route("/", methods=["GET"])
@login_required
def index():
    db = get_db()
    presences = db.execute(
        """
        SELECT p.id, u.name, p.day, p.arrival_time, p.departure_time
        FROM presences p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.day DESC, p.id DESC
        """
    ).fetchall()
    return render_template("index.html", presences=presences)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()
        user = db.execute(
            "SELECT id, name, password, is_admin FROM users WHERE name = ?",
            (name,),
        ).fetchone()

        if user and user["password"] == password:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_admin"] = bool(user["is_admin"])
            flash(f"Bienvenue {user['name']} !")
            return redirect(url_for("index"))

        flash("Identifiants invalides.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Déconnexion réussie.")
    return redirect(url_for("login"))


@app.route("/arrival", methods=["POST"])
@login_required
def arrival():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    user_id = session["user_id"]
    db = get_db()

    existing = db.execute(
        "SELECT id, arrival_time FROM presences WHERE user_id = ? AND day = ?",
        (user_id, today),
    ).fetchone()

    if existing and existing["arrival_time"]:
        flash("Arrivée déjà enregistrée pour aujourd'hui.")
    elif existing:
        db.execute(
            "UPDATE presences SET arrival_time = ? WHERE id = ?",
            (time_str, existing["id"]),
        )
        db.commit()
        flash(f"Arrivée enregistrée à {time_str}.")
    else:
        db.execute(
            "INSERT INTO presences (user_id, day, arrival_time) VALUES (?, ?, ?)",
            (user_id, today, time_str),
        )
        db.commit()
        flash(f"Arrivée enregistrée à {time_str}.")

    return redirect(url_for("index"))


@app.route("/departure", methods=["POST"])
@login_required
def departure():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    user_id = session["user_id"]
    db = get_db()

    existing = db.execute(
        "SELECT id, departure_time FROM presences WHERE user_id = ? AND day = ?",
        (user_id, today),
    ).fetchone()

    if existing and existing["departure_time"]:
        flash("Départ déjà enregistré pour aujourd'hui.")
    elif existing:
        db.execute(
            "UPDATE presences SET departure_time = ? WHERE id = ?",
            (time_str, existing["id"]),
        )
        db.commit()
        flash(f"Départ enregistré à {time_str}.")
    else:
        db.execute(
            "INSERT INTO presences (user_id, day, departure_time) VALUES (?, ?, ?)",
            (user_id, today, time_str),
        )
        db.commit()
        flash(f"Départ enregistré à {time_str}.")

    return redirect(url_for("index"))


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    today = datetime.now().strftime("%Y-%m-%d")
    today_arrivals = db.execute(
        "SELECT COUNT(*) AS total FROM presences WHERE day = ? AND arrival_time IS NOT NULL",
        (today,),
    ).fetchone()["total"]
    complete_days = db.execute(
        "SELECT COUNT(*) AS total FROM presences WHERE arrival_time IS NOT NULL AND departure_time IS NOT NULL"
    ).fetchone()["total"]

    recent = db.execute(
        """
        SELECT u.name, p.day, p.arrival_time, p.departure_time
        FROM presences p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.id DESC
        LIMIT 10
        """
    ).fetchall()

    return render_template(
        "admin.html",
        total_users=total_users,
        today_arrivals=today_arrivals,
        complete_days=complete_days,
        recent=recent,
    )


@app.route("/export/excel")
@login_required
@admin_required
def export_excel():
    db = get_db()
    rows = db.execute(
        """
        SELECT u.name, p.day, p.arrival_time, p.departure_time
        FROM presences p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.day DESC, u.name ASC
        """
    ).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Présences"
    ws.append(["Employé", "Date", "Heure arrivée", "Heure départ"])

    for row in rows:
        ws.append([row["name"], row["day"], row["arrival_time"], row["departure_time"]])

    export_path = BASE_DIR / "presences_export.xlsx"
    wb.save(export_path)

    return send_file(export_path, as_attachment=True, download_name="presences.xlsx")


@app.route("/api/presences", methods=["GET"])
@login_required
def api_list_presences():
    db = get_db()
    rows = db.execute(
        """
        SELECT p.id, u.name, p.day, p.arrival_time, p.departure_time
        FROM presences p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.id DESC
        """
    ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.route("/api/presences/arrival", methods=["POST"])
@login_required
def api_arrival():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    user_id = session["user_id"]
    db = get_db()

    existing = db.execute(
        "SELECT id, arrival_time FROM presences WHERE user_id = ? AND day = ?",
        (user_id, today),
    ).fetchone()

    if existing and existing["arrival_time"]:
        return jsonify({"message": "Arrivée déjà enregistrée"}), 409

    if existing:
        db.execute("UPDATE presences SET arrival_time = ? WHERE id = ?", (time_str, existing["id"]))
    else:
        db.execute(
            "INSERT INTO presences (user_id, day, arrival_time) VALUES (?, ?, ?)",
            (user_id, today, time_str),
        )
    db.commit()
    return jsonify({"message": "Arrivée enregistrée", "time": time_str}), 201


@app.route("/api/presences/departure", methods=["POST"])
@login_required
def api_departure():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    user_id = session["user_id"]
    db = get_db()

    existing = db.execute(
        "SELECT id, departure_time FROM presences WHERE user_id = ? AND day = ?",
        (user_id, today),
    ).fetchone()

    if existing and existing["departure_time"]:
        return jsonify({"message": "Départ déjà enregistré"}), 409

    if existing:
        db.execute("UPDATE presences SET departure_time = ? WHERE id = ?", (time_str, existing["id"]))
    else:
        db.execute(
            "INSERT INTO presences (user_id, day, departure_time) VALUES (?, ?, ?)",
            (user_id, today, time_str),
        )
    db.commit()
    return jsonify({"message": "Départ enregistré", "time": time_str}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
