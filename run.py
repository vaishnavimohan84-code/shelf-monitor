import os
from dotenv import load_dotenv

load_dotenv()  # explicitly load .env so it works with `python run.py` too, not just `flask run`

from app import create_app, db
from app.models.user import User

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("create-admin")
def create_admin():
    """Create a default admin user: flask --app run.py create-admin"""
    username = input("Admin username [admin]: ") or "admin"
    email = input("Admin email [admin@shelfmonitor.local]: ") or "admin@shelfmonitor.local"
    password = input("Admin password [admin123]: ") or "admin123"

    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists.")
        return

    user = User(username=username, email=email, role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Admin user '{username}' created successfully.")


@app.cli.command("init-db")
def init_db():
    """Create all tables from SQLAlchemy models: flask --app run.py init-db"""
    db.create_all()
    print("Database tables created.")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
