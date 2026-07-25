from datetime import datetime
from app import db


class DetectionLog(db.Model):
    """Stores the result of a single detection run (image upload or webcam capture)."""
    __tablename__ = "detection_logs"

    id = db.Column(db.Integer, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.id"), nullable=False)
    source_image = db.Column(db.String(255), nullable=False)
    annotated_image = db.Column(db.String(255), nullable=True)
    capture_type = db.Column(db.Enum("upload", "webcam", name="capture_type"), default="upload")
    total_products_detected = db.Column(db.Integer, default=0)
    empty_shelf_percentage = db.Column(db.Float, default=0.0)
    is_empty = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("DetectionItem", backref="log", lazy=True, cascade="all, delete-orphan")


class DetectionItem(db.Model):
    """Individual bounding-box detection belonging to a DetectionLog."""
    __tablename__ = "detection_items"

    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey("detection_logs.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    class_label = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    x1 = db.Column(db.Integer)
    y1 = db.Column(db.Integer)
    x2 = db.Column(db.Integer)
    y2 = db.Column(db.Integer)

    product = db.relationship("Product")


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    alert_type = db.Column(
        db.Enum("empty_shelf", "low_stock", "misplaced_product", name="alert_type"),
        nullable=False,
    )
    message = db.Column(db.String(255), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shelf = db.relationship("Shelf")
    product = db.relationship("Product")
