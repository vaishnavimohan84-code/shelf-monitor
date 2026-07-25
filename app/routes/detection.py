import os
import base64
import uuid
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.shelf import Shelf
from app.models.detection import DetectionLog, DetectionItem
from detection.detector import get_detector
from app.utils.shelf_analysis import (
    compute_shelf_coverage,
    match_products_by_class_label,
    evaluate_shelf_and_raise_alerts,
)

detection_bp = Blueprint("detection", __name__, url_prefix="/detection")


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _run_detection_pipeline(shelf_id, source_image_path, capture_type):
    """
    Shared pipeline used by both the upload and webcam routes:
      1. Run YOLOv8 inference (Step 7)
      2. Match detections to Product records + count them (Step 10)
      3. Compute shelf coverage / empty-shelf flag (Step 9)
      4. Persist DetectionLog + DetectionItem rows
      5. Raise low-stock / empty-shelf / misplaced-product alerts (Step 9-10)
      6. Save an annotated image for display
    Returns the created DetectionLog.
    """
    detector = get_detector(current_app.config)
    result = detector.detect(source_image_path)
    detections = match_products_by_class_label(result["detections"])

    coverage_ratio = compute_shelf_coverage(
        detections, result["image_width"], result["image_height"]
    )

    shelf = Shelf.query.get_or_404(shelf_id)

    log = DetectionLog(
        shelf_id=shelf.id,
        source_image=source_image_path.replace(current_app.static_folder + os.sep, ""),
        capture_type=capture_type,
        total_products_detected=len(detections),
        empty_shelf_percentage=round((1 - coverage_ratio) * 100, 2),
        created_by=current_user.id,
    )
    db.session.add(log)
    db.session.flush()  # get log.id before adding items

    for det in detections:
        item = DetectionItem(
            log_id=log.id,
            product_id=det.get("product_id"),
            class_label=det["class_label"],
            confidence=det["confidence"],
            x1=det["box"][0], y1=det["box"][1], x2=det["box"][2], y2=det["box"][3],
        )
        db.session.add(item)

    db.session.commit()

    is_empty, _alerts = evaluate_shelf_and_raise_alerts(
        shelf, detections, coverage_ratio, current_app.config["EMPTY_SHELF_THRESHOLD"]
    )
    log.is_empty = is_empty
    db.session.commit()

    # Annotated image (best-effort; if OpenCV/model isn't installed this simply
    # leaves annotated_image blank rather than breaking the whole request).
    try:
        annotated_name = f"annotated_{uuid.uuid4().hex}.jpg"
        annotated_path = os.path.join(current_app.config["CAPTURE_FOLDER"], annotated_name)
        detector.annotate(source_image_path, detections, annotated_path)
        log.annotated_image = f"captures/{annotated_name}"
        db.session.commit()
    except Exception as exc:  # pragma: no cover - best effort only
        current_app.logger.warning(f"Could not generate annotated image: {exc}")

    return log


@detection_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    shelves = Shelf.query.order_by(Shelf.name).all()

    if request.method == "POST":
        shelf_id = request.form.get("shelf_id")
        file_storage = request.files.get("image")

        if not shelf_id:
            flash("Please select a shelf.", "danger")
            return redirect(url_for("detection.upload"))

        if not file_storage or file_storage.filename == "":
            flash("Please choose an image to upload.", "danger")
            return redirect(url_for("detection.upload"))

        if not _allowed_file(file_storage.filename):
            flash("Invalid image type. Allowed: png, jpg, jpeg.", "danger")
            return redirect(url_for("detection.upload"))

        safe_name = secure_filename(file_storage.filename)
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
        file_storage.save(dest_path)

        try:
            log = _run_detection_pipeline(int(shelf_id), dest_path, "upload")
        except FileNotFoundError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("detection.upload"))
        except ImportError:
            flash(
                "YOLOv8 dependencies (ultralytics/opencv) are not installed in this "
                "environment. Install requirements.txt to enable detection.",
                "danger",
            )
            return redirect(url_for("detection.upload"))

        return redirect(url_for("detection.result", log_id=log.id))

    return render_template("dashboard/detect_upload.html", shelves=shelves)


@detection_bp.route("/webcam", methods=["GET", "POST"])
@login_required
def webcam():
    shelves = Shelf.query.order_by(Shelf.name).all()

    if request.method == "POST":
        shelf_id = request.form.get("shelf_id")
        image_data_url = request.form.get("image_data")

        if not shelf_id:
            flash("Please select a shelf.", "danger")
            return redirect(url_for("detection.webcam"))

        if not image_data_url or "," not in image_data_url:
            flash("No webcam frame captured. Please capture an image first.", "danger")
            return redirect(url_for("detection.webcam"))

        header, encoded = image_data_url.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        unique_name = f"{uuid.uuid4().hex}_webcam.jpg"
        dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
        with open(dest_path, "wb") as f:
            f.write(image_bytes)

        try:
            log = _run_detection_pipeline(int(shelf_id), dest_path, "webcam")
        except FileNotFoundError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("detection.webcam"))
        except ImportError:
            flash(
                "YOLOv8 dependencies (ultralytics/opencv) are not installed in this "
                "environment. Install requirements.txt to enable detection.",
                "danger",
            )
            return redirect(url_for("detection.webcam"))

        return redirect(url_for("detection.result", log_id=log.id))

    return render_template("dashboard/detect_webcam.html", shelves=shelves)


@detection_bp.route("/result/<int:log_id>")
@login_required
def result(log_id):
    log = DetectionLog.query.get_or_404(log_id)
    return render_template("dashboard/detect_result.html", log=log)


@detection_bp.route("/history")
@login_required
def history():
    shelf_id = request.args.get("shelf_id", type=int)
    query = DetectionLog.query
    if shelf_id:
        query = query.filter_by(shelf_id=shelf_id)
    logs = query.order_by(DetectionLog.created_at.desc()).limit(100).all()
    shelves = Shelf.query.order_by(Shelf.name).all()
    return render_template("dashboard/detect_history.html", logs=logs, shelves=shelves, selected_shelf_id=shelf_id)
