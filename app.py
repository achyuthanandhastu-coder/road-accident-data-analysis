import os
from datetime import datetime
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from config import Config
from database import get_connection, init_db
from services.analysis import (
    build_dashboard_data, build_location_summary, build_time_summary,
    build_severity_summary, build_charts
)
from services.validation import validate_accident_row, normalize_datetime

app = Flask(__name__)
app.config.from_object(Config)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.template_filter("number")
def number_filter(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


@app.route("/")
def dashboard():
    try:
        data = build_dashboard_data()
        chart_paths = build_charts(data["records"])
        return render_template("dashboard.html", data=data, chart_paths=chart_paths)
    except Exception as exc:
        app.logger.exception("Dashboard failed")
        flash(f"Could not load dashboard. Check MySQL settings and connection. Details: {exc}", "error")
        return render_template("dashboard.html", data=None, chart_paths={})


@app.route("/accidents")
def accidents():
    search = request.args.get("search", "").strip()
    severity = request.args.get("severity", "").strip()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT a.accident_id, a.accident_datetime, l.region, l.road_name,
                   a.vehicle_type, a.severity, a.weather
            FROM accidents a
            JOIN locations l ON l.location_id = a.location_id
            WHERE (%s = '' OR l.region LIKE %s OR l.road_name LIKE %s OR a.vehicle_type LIKE %s)
              AND (%s = '' OR a.severity = %s)
            ORDER BY a.accident_datetime DESC
            LIMIT 500
        """
        like = f"%{search}%"
        cursor.execute(sql, (search, like, like, like, severity, severity))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("accidents.html", records=records, search=search, severity=severity)
    except Exception as exc:
        app.logger.exception("Accident list failed")
        flash(f"Could not read accident records: {exc}", "error")
        return render_template("accidents.html", records=[], search=search, severity=severity)


@app.route("/accidents/add", methods=["GET", "POST"])
def add_accident():
    if request.method == "POST":
        row = {
            "accident_datetime": request.form.get("accident_datetime", "").strip(),
            "region": request.form.get("region", "").strip(),
            "road_name": request.form.get("road_name", "").strip(),
            "vehicle_type": request.form.get("vehicle_type", "").strip(),
            "severity": request.form.get("severity", "").strip(),
            "weather": request.form.get("weather", "").strip() or None,
        }
        errors = validate_accident_row(row)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("accident_form.html", row=row)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO locations (region, road_name) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE location_id=LAST_INSERT_ID(location_id)",
                (row["region"], row["road_name"] or None),
            )
            location_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO accidents
                   (accident_datetime, location_id, vehicle_type, severity, weather)
                   VALUES (%s, %s, %s, %s, %s)""",
                (normalize_datetime(row["accident_datetime"]), location_id,
                 row["vehicle_type"], row["severity"], row["weather"]),
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Accident record added successfully.", "success")
            return redirect(url_for("accidents"))
        except Exception as exc:
            app.logger.exception("Add accident failed")
            flash(f"Could not save record: {exc}", "error")
    else:
        row = {}
    return render_template("accident_form.html", row=row)


@app.route("/upload", methods=["GET", "POST"])
def upload_csv():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Choose a CSV file first.", "error")
            return redirect(url_for("upload_csv"))
        if not allowed_file(file.filename):
            flash("Only .csv files are accepted.", "error")
            return redirect(url_for("upload_csv"))

        try:
            df = pd.read_csv(file)
            required = {"accident_datetime", "region", "vehicle_type", "severity"}
            missing_columns = required - set(df.columns)
            if missing_columns:
                flash("CSV is missing required columns: " + ", ".join(sorted(missing_columns)), "error")
                return redirect(url_for("upload_csv"))

            inserted, rejected, issues = 0, 0, []
            conn = get_connection()
            cursor = conn.cursor()
            for index, source_row in df.iterrows():
                row = {key: (None if pd.isna(value) else str(value).strip())
                       for key, value in source_row.to_dict().items()}
                row.setdefault("road_name", None)
                row.setdefault("weather", None)
                errors = validate_accident_row(row)
                if errors:
                    rejected += 1
                    if len(issues) < 12:
                        issues.append(f"CSV row {index + 2}: " + "; ".join(errors))
                    continue
                cursor.execute(
                    "INSERT INTO locations (region, road_name) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE location_id=LAST_INSERT_ID(location_id)",
                    (row["region"], row.get("road_name") or None),
                )
                location_id = cursor.lastrowid
                cursor.execute(
                    """INSERT INTO accidents
                       (accident_datetime, location_id, vehicle_type, severity, weather)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (normalize_datetime(row["accident_datetime"]), location_id,
                     row["vehicle_type"], row["severity"], row.get("weather") or None),
                )
                inserted += 1
            conn.commit()
            cursor.close()
            conn.close()
            flash(f"Import complete: {inserted} inserted, {rejected} rejected.", "success")
            for issue in issues:
                flash(issue, "warning")
            if rejected > len(issues):
                flash(f"{rejected - len(issues)} additional rejected rows were not displayed.", "warning")
            return redirect(url_for("accidents"))
        except Exception as exc:
            app.logger.exception("CSV import failed")
            flash(f"CSV import failed: {exc}", "error")
            return redirect(url_for("upload_csv"))
    return render_template("upload.html")


@app.route("/reports")
def reports():
    try:
        data = build_dashboard_data()
        return render_template(
            "reports.html",
            data=data,
            time_summary=build_time_summary(data["records"]),
            location_summary=build_location_summary(data["records"]),
            severity_summary=build_severity_summary(data["records"]),
        )
    except Exception as exc:
        app.logger.exception("Reports failed")
        flash(f"Could not create report: {exc}", "error")
        return render_template("reports.html", data=None, time_summary=[], location_summary=[],
                               severity_summary=[])


@app.route("/charts/<chart_name>.png")
def chart_image(chart_name):
    if chart_name not in {"daily", "severity", "vehicle"}:
        return "Chart not found", 404
    try:
        data = build_dashboard_data()
        charts = build_charts(data["records"], return_bytes=True)
        return send_file(BytesIO(charts[chart_name]), mimetype="image/png")
    except Exception as exc:
        app.logger.exception("Chart generation failed")
        return f"Could not generate chart: {exc}", 500


@app.route("/health")
def health():
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}, 200
    except Exception as exc:
        return {"status": "error", "database": "unavailable", "detail": str(exc)}, 503


if __name__ == "__main__":
    if os.getenv("INIT_DB", "true").lower() == "true":
        init_db()
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
