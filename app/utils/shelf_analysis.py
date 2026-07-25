"""
Business logic for turning raw YOLOv8 detections into shelf-level insight:
- empty / low-stock shelf detection (Step 9)
- per-product counting vs. planogram expectations (Step 10)
- alert creation for empty shelves, low stock, and misplaced products
"""
from app import db
from app.models.product import Product
from app.models.shelf import ShelfProduct
from app.models.detection import Alert


def compute_shelf_coverage(detections, image_width, image_height):
    """
    Empty-shelf heuristic: sum the area of all detected bounding boxes and
    divide by total image area. A low ratio means most of the shelf is bare.

    Returns (coverage_ratio, is_empty) where is_empty is True when coverage
    falls below the configured EMPTY_SHELF_THRESHOLD.
    """
    image_area = max(image_width * image_height, 1)
    total_box_area = 0
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        total_box_area += max(0, x2 - x1) * max(0, y2 - y1)

    coverage_ratio = min(total_box_area / image_area, 1.0)
    return coverage_ratio


def match_products_by_class_label(detections):
    """Attaches a product_id to each detection dict by matching class_label -> Product.class_label."""
    labels = {d["class_label"] for d in detections}
    if not labels:
        return detections

    products = Product.query.filter(Product.class_label.in_(labels)).all()
    label_to_product = {p.class_label: p for p in products}

    for det in detections:
        product = label_to_product.get(det["class_label"])
        det["product_id"] = product.id if product else None

    return detections


def count_products(detections):
    """Returns {class_label: count} across all detections in a single scan."""
    counts = {}
    for det in detections:
        counts[det["class_label"]] = counts.get(det["class_label"], 0) + 1
    return counts


def evaluate_shelf_and_raise_alerts(shelf, detections, coverage_ratio, empty_threshold, app_config=None):
    """
    Core Step 9/10 logic:
      1. Flags the shelf as empty if coverage_ratio < empty_threshold.
      2. Compares detected counts per product against the shelf's planogram
         (ShelfProduct.expected_quantity) and raises low-stock alerts.

    Returns (is_empty: bool, created_alerts: list[Alert])
    """
    created_alerts = []
    is_empty = coverage_ratio < empty_threshold

    if is_empty:
        alert = Alert(
            shelf_id=shelf.id,
            product_id=None,
            alert_type="empty_shelf",
            message=(
                f"Shelf '{shelf.name}' appears empty or nearly empty "
                f"(only {coverage_ratio * 100:.1f}% shelf coverage detected)."
            ),
        )
        db.session.add(alert)
        created_alerts.append(alert)

    counts = count_products(detections)

    planogram_entries = ShelfProduct.query.filter_by(shelf_id=shelf.id).all()
    for entry in planogram_entries:
        product = entry.product
        detected_qty = counts.get(product.class_label, 0)

        if detected_qty < product.min_stock_threshold:
            alert = Alert(
                shelf_id=shelf.id,
                product_id=product.id,
                alert_type="low_stock",
                message=(
                    f"Low stock for '{product.name}' on shelf '{shelf.name}': "
                    f"detected {detected_qty}, expected around {entry.expected_quantity} "
                    f"(minimum threshold {product.min_stock_threshold})."
                ),
            )
            db.session.add(alert)
            created_alerts.append(alert)

    # Misplaced product: detected a class_label that maps to a known product
    # but that product isn't in this shelf's planogram at all.
    planogram_product_ids = {e.product_id for e in planogram_entries}
    detected_class_labels = set(counts.keys())
    known_products = Product.query.filter(Product.class_label.in_(detected_class_labels)).all()
    for product in known_products:
        if product.id not in planogram_product_ids:
            alert = Alert(
                shelf_id=shelf.id,
                product_id=product.id,
                alert_type="misplaced_product",
                message=(
                    f"'{product.name}' detected on shelf '{shelf.name}' but is not part of "
                    "this shelf's planogram — possible misplaced product."
                ),
            )
            db.session.add(alert)
            created_alerts.append(alert)

    db.session.commit()
    return is_empty, created_alerts
