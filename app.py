"""ACEest Fitness & Gym - Flask web application."""

import os
import sqlite3
from datetime import date

from flask import Flask, jsonify, render_template, request

from fitness import db
from fitness.calculations import calculate_bmi, estimate_calories, validate_adherence
from fitness.programs import PROGRAMS, get_program, list_programs


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("ACEEST_DB", os.path.join(app.instance_path, "aceest.db")),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]) or ".", exist_ok=True)
    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()

    register_routes(app)
    return app


def error(message, status=400):
    return jsonify({"error": message}), status


def client_exists(conn, name):
    return conn.execute("SELECT 1 FROM clients WHERE name = ?", (name,)).fetchone() is not None


def register_routes(app):
    @app.get("/")
    def home():
        return render_template("index.html", programs=PROGRAMS)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------- Programs ----------
    @app.get("/api/programs")
    def programs():
        return jsonify(list_programs())

    @app.get("/api/programs/<code>")
    def program_detail(code):
        program = get_program(code)
        if program is None:
            return error(f"Program '{code}' not found", 404)
        return jsonify(program)

    # ---------- Calculators ----------
    @app.post("/api/calories")
    def calories():
        data = request.get_json(silent=True) or {}
        try:
            kcal = estimate_calories(data.get("weight_kg"), data.get("program"))
        except ValueError as exc:
            return error(str(exc))
        return jsonify({"calories": kcal})

    @app.post("/api/bmi")
    def bmi():
        data = request.get_json(silent=True) or {}
        try:
            value, category = calculate_bmi(data.get("height_cm"), data.get("weight_kg"))
        except ValueError as exc:
            return error(str(exc))
        return jsonify({"bmi": value, "category": category})

    # ---------- Clients ----------
    @app.get("/api/clients")
    def clients():
        rows = db.get_db().execute("SELECT * FROM clients ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/api/clients")
    def create_client():
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        if not name:
            return error("name is required")
        program = data.get("program")
        calories_value = None
        if program is not None:
            if get_program(program) is None:
                return error(f"Unknown program '{program}'")
            program = program.upper()
            if data.get("weight") is not None:
                try:
                    calories_value = estimate_calories(data["weight"], program)
                except ValueError as exc:
                    return error(str(exc))
        conn = db.get_db()
        try:
            conn.execute(
                "INSERT INTO clients (name, age, height, weight, program, calories, membership_end)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, data.get("age"), data.get("height"), data.get("weight"),
                 program, calories_value, data.get("membership_end")),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return error(f"Client '{name}' already exists", 409)
        row = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
        return jsonify(dict(row)), 201

    @app.get("/api/clients/<name>")
    def client_detail(name):
        row = db.get_db().execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
        if row is None:
            return error(f"Client '{name}' not found", 404)
        return jsonify(dict(row))

    @app.get("/api/clients/<name>/membership")
    def membership(name):
        row = db.get_db().execute(
            "SELECT membership_status, membership_end FROM clients WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return error(f"Client '{name}' not found", 404)
        status = row["membership_status"]
        end = row["membership_end"]
        if end:
            try:
                if date.fromisoformat(end) < date.today():
                    status = "Expired"
            except ValueError:
                pass
        return jsonify({"client": name, "status": status, "renewal_date": end})

    # ---------- Progress ----------
    @app.route("/api/clients/<name>/progress", methods=["GET", "POST"])
    def progress(name):
        conn = db.get_db()
        if not client_exists(conn, name):
            return error(f"Client '{name}' not found", 404)
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            week = str(data.get("week", "")).strip()
            if not week:
                return error("week is required")
            try:
                adherence = validate_adherence(data.get("adherence"))
            except ValueError as exc:
                return error(str(exc))
            conn.execute(
                "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
                (name, week, adherence),
            )
            conn.commit()
            return jsonify({"client": name, "week": week, "adherence": adherence}), 201
        rows = conn.execute(
            "SELECT week, adherence FROM progress WHERE client_name = ? ORDER BY id", (name,)
        ).fetchall()
        entries = [dict(r) for r in rows]
        average = round(sum(e["adherence"] for e in entries) / len(entries), 1) if entries else None
        return jsonify({"client": name, "entries": entries, "average_adherence": average})

    # ---------- Workouts ----------
    @app.route("/api/clients/<name>/workouts", methods=["GET", "POST"])
    def workouts(name):
        conn = db.get_db()
        if not client_exists(conn, name):
            return error(f"Client '{name}' not found", 404)
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            workout_type = str(data.get("workout_type", "")).strip()
            if not workout_type:
                return error("workout_type is required")
            duration = data.get("duration_min")
            if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
                return error("duration_min must be a positive integer")
            workout_date = data.get("date") or date.today().isoformat()
            conn.execute(
                "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)"
                " VALUES (?, ?, ?, ?, ?)",
                (name, workout_date, workout_type, duration, data.get("notes", "")),
            )
            conn.commit()
            return jsonify({"client": name, "date": workout_date,
                            "workout_type": workout_type, "duration_min": duration}), 201
        rows = conn.execute(
            "SELECT date, workout_type, duration_min, notes FROM workouts"
            " WHERE client_name = ? ORDER BY date DESC", (name,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
