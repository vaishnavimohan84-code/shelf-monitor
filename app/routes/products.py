import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.product import Product

products_bp = Blueprint("products", __name__, url_prefix="/products")


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _save_product_image(file_storage):
    """Saves an uploaded product image and returns its relative static path, or None."""
    if not file_storage or file_storage.filename == "":
        return None
    if not _allowed_file(file_storage.filename):
        flash("Invalid image type. Allowed: png, jpg, jpeg.", "warning")
        return None
    safe_name = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(dest_path)
    return f"uploads/{unique_name}"


@products_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Product.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(like),
                Product.sku.ilike(like),
                Product.class_label.ilike(like),
            )
        )
    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.name).all()

    # Distinct categories for the filter dropdown
    categories = [
        c[0] for c in db.session.query(Product.category).distinct() if c[0]
    ]

    return render_template(
        "products/index.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category,
    )


def _all_categories():
    return [c[0] for c in db.session.query(Product.category).distinct() if c[0]]


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        category = request.form.get("category", "").strip()
        class_label = request.form.get("class_label", "").strip()
        min_stock_threshold = request.form.get("min_stock_threshold", "5") or "5"

        if not name or not sku or not class_label:
            flash("Name, SKU and Class Label are required.", "danger")
            return render_template("products/form.html", product=None, form_data=request.form, categories=_all_categories())

        if Product.query.filter_by(sku=sku).first():
            flash(f"A product with SKU '{sku}' already exists.", "danger")
            return render_template("products/form.html", product=None, form_data=request.form, categories=_all_categories())

        image_path = _save_product_image(request.files.get("image"))

        product = Product(
            name=name,
            sku=sku,
            category=category or None,
            class_label=class_label,
            min_stock_threshold=int(min_stock_threshold),
            image_path=image_path,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Product '{name}' created.", "success")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", product=None, form_data=None, categories=_all_categories())


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        category = request.form.get("category", "").strip()
        class_label = request.form.get("class_label", "").strip()
        min_stock_threshold = request.form.get("min_stock_threshold", "5") or "5"

        if not name or not sku or not class_label:
            flash("Name, SKU and Class Label are required.", "danger")
            return render_template("products/form.html", product=product, form_data=request.form, categories=_all_categories())

        duplicate = Product.query.filter(Product.sku == sku, Product.id != product.id).first()
        if duplicate:
            flash(f"Another product already uses SKU '{sku}'.", "danger")
            return render_template("products/form.html", product=product, form_data=request.form, categories=_all_categories())

        new_image_path = _save_product_image(request.files.get("image"))
        if new_image_path:
            product.image_path = new_image_path

        product.name = name
        product.sku = sku
        product.category = category or None
        product.class_label = class_label
        product.min_stock_threshold = int(min_stock_threshold)
        db.session.commit()
        flash(f"Product '{name}' updated.", "success")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", product=product, form_data=None, categories=_all_categories())


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{name}' deleted.", "info")
    return redirect(url_for("products.index"))
