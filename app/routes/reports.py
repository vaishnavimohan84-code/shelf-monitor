from datetime import datetime

from flask import Blueprint, render_template, request, send_from_directory, current_app, flash, redirect, url_for
from flask_login import login_required

from app.models.shelf import Shelf
from app.utils.report_generator import generate_csv_report, generate_excel_report, generate_pdf_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


@reports_bp.route("/")
@login_required
def index():
    shelves = Shelf.query.order_by(Shelf.name).all()
    return render_template("reports/index.html", shelves=shelves)


@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    report_format = request.form.get("format", "pdf")
    start_date = _parse_date(request.form.get("start_date"))
    end_date = _parse_date(request.form.get("end_date"))
    shelf_id = request.form.get("shelf_id") or None
    shelf_id = int(shelf_id) if shelf_id else None

    reports_folder = current_app.config["REPORTS_FOLDER"]

    try:
        if report_format == "csv":
            filename = generate_csv_report(reports_folder, start_date, end_date, shelf_id)
        elif report_format == "excel":
            filename = generate_excel_report(reports_folder, start_date, end_date, shelf_id)
        else:
            filename = generate_pdf_report(reports_folder, start_date, end_date, shelf_id)
    except ImportError as exc:
        flash(
            f"Report dependency missing ({exc}). Install requirements.txt "
            "(reportlab / openpyxl) to enable this export format.",
            "danger",
        )
        return redirect(url_for("reports.index"))

    return redirect(url_for("reports.download", filename=filename))


@reports_bp.route("/download/<path:filename>")
@login_required
def download(filename):
    reports_folder = current_app.config["REPORTS_FOLDER"]
    return send_from_directory(reports_folder, filename, as_attachment=True)
