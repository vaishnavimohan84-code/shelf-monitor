from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/users")


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper


@users_bp.route("/")
@login_required
@admin_required
def index():
    users = User.query.order_by(User.username).all()
    return render_template("dashboard/users.html", users=users)


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "staff")

        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return render_template("users/form.html", user=None, form_data=request.form)

        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template("users/form.html", user=None, form_data=request.form)

        if User.query.filter_by(email=email).first():
            flash(f"Email '{email}' is already registered.", "danger")
            return render_template("users/form.html", user=None, form_data=request.form)

        user = User(username=username, email=email, role=role if role in ("admin", "staff") else "staff")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"User '{username}' created.", "success")
        return redirect(url_for("users.index"))

    return render_template("users/form.html", user=None, form_data=None)


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "staff")
        new_password = request.form.get("password", "")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("users/form.html", user=user, form_data=request.form)

        duplicate_username = User.query.filter(User.username == username, User.id != user.id).first()
        if duplicate_username:
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template("users/form.html", user=user, form_data=request.form)

        duplicate_email = User.query.filter(User.email == email, User.id != user.id).first()
        if duplicate_email:
            flash(f"Email '{email}' is already registered.", "danger")
            return render_template("users/form.html", user=user, form_data=request.form)

        user.username = username
        user.email = email
        user.role = role if role in ("admin", "staff") else "staff"
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash(f"User '{username}' updated.", "success")
        return redirect(url_for("users.index"))

    return render_template("users/form.html", user=user, form_data=None)


@users_bp.route("/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't deactivate your own account.", "warning")
        return redirect(url_for("users.index"))

    user.is_active_user = not user.is_active_user
    db.session.commit()
    flash(f"User '{user.username}' {'activated' if user.is_active_user else 'deactivated'}.", "info")
    return redirect(url_for("users.index"))


@users_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "warning")
        return redirect(url_for("users.index"))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{username}' deleted.", "info")
    return redirect(url_for("users.index"))


@users_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Any logged-in user (admin or staff) can change their own password."""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return render_template("users/change_password.html")

        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "danger")
            return render_template("users/change_password.html")

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return render_template("users/change_password.html")

        current_user.set_password(new_password)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("users/change_password.html")
