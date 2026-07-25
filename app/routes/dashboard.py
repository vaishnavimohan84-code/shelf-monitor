from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models.product import Product
from app.models.shelf import Shelf
from app.models.detection import DetectionLog, Alert

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _detections_per_day(days=7):
    """Returns (labels, counts) for the last `days` days, oldest first."""
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days - 1)

    rows = (
        db.session.query(
            func.date(DetectionLog.created_at).label("day"),
            func.count(DetectionLog.id).label("total"),
        )
        .filter(func.date(DetectionLog.created_at) >= start_date)
        .group_by("day")
        .all()
    )
    counts_by_day = {str(r.day): r.total for r in rows}

    labels, counts = [], []
    for i in range(days):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime("%b %d"))
        counts.append(counts_by_day.get(str(day), 0))

    return labels, counts


def _alerts_breakdown():
    rows = (
        db.session.query(Alert.alert_type, func.count(Alert.id))
        .filter(Alert.is_resolved.is_(False))
        .group_by(Alert.alert_type)
        .all()
    )
    breakdown = {row[0]: row[1] for row in rows}
    return {
        "empty_shelf": breakdown.get("empty_shelf", 0),
        "low_stock": breakdown.get("low_stock", 0),
        "misplaced_product": breakdown.get("misplaced_product", 0),
    }


def _top_scanned_shelves(limit=5):
    rows = (
        db.session.query(Shelf.name, func.count(DetectionLog.id).label("scans"))
        .join(DetectionLog, DetectionLog.shelf_id == Shelf.id)
        .group_by(Shelf.id)
        .order_by(func.count(DetectionLog.id).desc())
        .limit(limit)
        .all()
    )
    return [r.name for r in rows], [r.scans for r in rows]


@dashboard_bp.route("/")
@login_required
def index():
    total_products = Product.query.count()
    total_shelves = Shelf.query.count()
    total_scans = DetectionLog.query.count()
    open_alerts = Alert.query.filter_by(is_resolved=False).count()
    empty_shelf_count = DetectionLog.query.filter_by(is_empty=True).count()

    recent_logs = (
        DetectionLog.query.order_by(DetectionLog.created_at.desc()).limit(5).all()
    )
    recent_alerts = (
        Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    )

    kpis = {
        "total_products": total_products,
        "total_shelves": total_shelves,
        "total_scans": total_scans,
        "open_alerts": open_alerts,
        "empty_shelf_count": empty_shelf_count,
    }

    trend_labels, trend_counts = _detections_per_day(days=7)
    alerts_breakdown = _alerts_breakdown()
    top_shelf_labels, top_shelf_counts = _top_scanned_shelves(limit=5)

    return render_template(
        "dashboard/index.html",
        kpis=kpis,
        recent_logs=recent_logs,
        recent_alerts=recent_alerts,
        trend_labels=trend_labels,
        trend_counts=trend_counts,
        alerts_breakdown=alerts_breakdown,
        top_shelf_labels=top_shelf_labels,
        top_shelf_counts=top_shelf_counts,
    )
