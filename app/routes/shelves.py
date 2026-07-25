from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.models.shelf import Shelf, ShelfProduct
from app.models.product import Product

shelves_bp = Blueprint("shelves", __name__, url_prefix="/shelves")


@shelves_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    query = Shelf.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Shelf.name.ilike(like), Shelf.location.ilike(like), Shelf.aisle.ilike(like))
        )
    shelves = query.order_by(Shelf.name).all()
    return render_template("shelves/index.html", shelves=shelves, search=search)


@shelves_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        aisle = request.form.get("aisle", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Shelf name is required.", "danger")
            return render_template("shelves/form.html", shelf=None, form_data=request.form)

        shelf = Shelf(name=name, location=location or None, aisle=aisle or None, description=description or None)
        db.session.add(shelf)
        db.session.commit()
        flash(f"Shelf '{name}' created.", "success")
        return redirect(url_for("shelves.index"))

    return render_template("shelves/form.html", shelf=None, form_data=None)


@shelves_bp.route("/<int:shelf_id>/edit", methods=["GET", "POST"])
@login_required
def edit(shelf_id):
    shelf = Shelf.query.get_or_404(shelf_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        aisle = request.form.get("aisle", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Shelf name is required.", "danger")
            return render_template("shelves/form.html", shelf=shelf, form_data=request.form)

        shelf.name = name
        shelf.location = location or None
        shelf.aisle = aisle or None
        shelf.description = description or None
        db.session.commit()
        flash(f"Shelf '{name}' updated.", "success")
        return redirect(url_for("shelves.index"))

    return render_template("shelves/form.html", shelf=shelf, form_data=None)


@shelves_bp.route("/<int:shelf_id>/delete", methods=["POST"])
@login_required
def delete(shelf_id):
    shelf = Shelf.query.get_or_404(shelf_id)
    name = shelf.name
    db.session.delete(shelf)
    db.session.commit()
    flash(f"Shelf '{name}' deleted.", "info")
    return redirect(url_for("shelves.index"))


@shelves_bp.route("/<int:shelf_id>/planogram", methods=["GET", "POST"])
@login_required
def planogram(shelf_id):
    """Assign expected products + quantities to a shelf (used by empty-shelf / low-stock logic)."""
    shelf = Shelf.query.get_or_404(shelf_id)

    if request.method == "POST":
        product_id = request.form.get("product_id")
        expected_quantity = request.form.get("expected_quantity", "10") or "10"

        if not product_id:
            flash("Please select a product.", "danger")
            return redirect(url_for("shelves.planogram", shelf_id=shelf.id))

        existing = ShelfProduct.query.filter_by(shelf_id=shelf.id, product_id=product_id).first()
        if existing:
            existing.expected_quantity = int(expected_quantity)
            flash("Planogram entry updated.", "success")
        else:
            entry = ShelfProduct(
                shelf_id=shelf.id,
                product_id=int(product_id),
                expected_quantity=int(expected_quantity),
            )
            db.session.add(entry)
            flash("Product added to planogram.", "success")

        db.session.commit()
        return redirect(url_for("shelves.planogram", shelf_id=shelf.id))

    assigned_product_ids = {sp.product_id for sp in shelf.planogram}
    available_products = Product.query.filter(~Product.id.in_(assigned_product_ids)).order_by(Product.name).all() \
        if assigned_product_ids else Product.query.order_by(Product.name).all()

    return render_template(
        "shelves/planogram.html",
        shelf=shelf,
        entries=shelf.planogram,
        available_products=available_products,
    )


@shelves_bp.route("/<int:shelf_id>/planogram/<int:entry_id>/remove", methods=["POST"])
@login_required
def planogram_remove(shelf_id, entry_id):
    entry = ShelfProduct.query.get_or_404(entry_id)
    if entry.shelf_id != shelf_id:
        flash("Invalid planogram entry.", "danger")
        return redirect(url_for("shelves.planogram", shelf_id=shelf_id))
    db.session.delete(entry)
    db.session.commit()
    flash("Product removed from planogram.", "info")
    return redirect(url_for("shelves.planogram", shelf_id=shelf_id))
