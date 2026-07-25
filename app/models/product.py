from datetime import datetime
from app import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    class_label = db.Column(db.String(100), nullable=False)
    # class_label must match the YOLO model's trained class name for this product
    min_stock_threshold = db.Column(db.Integer, default=5)
    image_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Product {self.name} ({self.sku})>"
