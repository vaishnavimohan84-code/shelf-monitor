import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config_map

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Ensure required folders exist
    for folder_key in ("UPLOAD_FOLDER", "CAPTURE_FOLDER", "REPORTS_FOLDER"):
        os.makedirs(app.config[folder_key], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

        from app.models.user import User

        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", email="admin@shelfmonitor.local", role="admin")
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            db.session.commit()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ---- Register blueprints ----
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.shelves import shelves_bp
    from app.routes.detection import detection_bp
    from app.routes.reports import reports_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(shelves_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)

    # ---- Root route ----
    # Visiting "/" directly (e.g. http://localhost:5000/) previously 404'd
    # because no blueprint owns the bare root path. Redirect it somewhere useful.
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # ---- User loader for Flask-Login ----
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---- Error handlers ----
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    return app
