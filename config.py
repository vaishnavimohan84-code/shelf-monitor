import os
from datetime import timedelta
from urllib.parse import quote

import pymysql

basedir = os.path.abspath(os.path.dirname(__file__))


def build_database_uri():
    if os.environ.get("DB_USE_SQLITE", "false").lower() in {"1", "true", "yes", "on"}:
        return f"sqlite:///{os.path.join(basedir, 'app.db')}"

    if os.environ.get("DB_SKIP_CONNECTION_CHECK", "false").lower() in {"1", "true", "yes", "on"}:
        DB_HOST = os.environ.get("DB_HOST", "localhost")
        DB_USER = os.environ.get("DB_USER", "root")
        DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
        DB_NAME = os.environ.get("DB_NAME", "shelf_monitor")
        DB_PORT = int(os.environ.get("DB_PORT", 3306))
        return (
            "mysql+pymysql://"
            f"{quote(DB_USER)}:{quote(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "shelf_monitor")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            connect_timeout=2,
        )
        connection.close()
    except Exception:
        return f"sqlite:///{os.path.join(basedir, 'app.db')}"

    return (
        "mysql+pymysql://"
        f"{quote(DB_USER)}:{quote(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


class Config:
    # ---- Core Flask ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ---- Database ----
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- File Uploads ----
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    CAPTURE_FOLDER = os.path.join(basedir, "app", "static", "captures")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # ---- YOLOv8 Model ----
    YOLO_MODEL_PATH = os.environ.get(
        "YOLO_MODEL_PATH", os.path.join(basedir, "detection", "best.pt")
    )
    YOLO_CONFIDENCE_THRESHOLD = float(os.environ.get("YOLO_CONF", 0.4))

    # ---- Empty Shelf Detection ----
    EMPTY_SHELF_THRESHOLD = float(os.environ.get("EMPTY_SHELF_THRESHOLD", 0.15))
    # If detected product area / shelf area < threshold -> considered empty/low stock

    # ---- Reports ----
    REPORTS_FOLDER = os.path.join(basedir, "app", "static", "reports")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
