from datetime import datetime
from app import db


class Shelf(db.Model):
    __tablename__ = "shelves"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    aisle = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scans = db.relationship("DetectionLog", backref="shelf", lazy=True)

    def __repr__(self):
        return f"<Shelf {self.name}>"


class ShelfProduct(db.Model):
    """Defines which products are expected on which shelf (planogram)."""
    __tablename__ = "shelf_products"

    id = db.Column(db.Integer, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    expected_quantity = db.Column(db.Integer, default=10)

    shelf = db.relationship("Shelf", backref="planogram")
    product = db.relationship("Product")
