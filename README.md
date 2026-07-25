# AI Product Shelf Monitoring System

Flask + MySQL + YOLOv8 web application that detects products on retail
shelves from an uploaded image or webcam capture, counts stock, flags
empty/low-stock shelves, and generates analytics + reports.

## Build status

All 14 planned modules are implemented:

| Step | Module | Status |
|---|---|---|
| 1 | Project structure & Flask app factory | Done |
| 2 | MySQL schema + seed data | Done |
| 3 | Login & authentication (Flask-Login) | Done |
| 4 | Admin dashboard (KPIs, recent scans/alerts) | Done |
| 5 | Product management (full CRUD, search, category filter, image upload) | Done |
| 6 | Shelf management (full CRUD + planogram assignment) | Done |
| 7 | YOLOv8 integration (`detection/detector.py`) | Done |
| 8 | Product detection — image upload | Done |
| 9 | Empty shelf detection (coverage-ratio heuristic + alerts) | Done |
| 10 | Product counting vs. planogram + low-stock/misplaced alerts | Done |
| 11 | Analytics dashboard (Chart.js: scan trend, alert breakdown, top shelves) | Done |
| 12 | Report generation (PDF via reportlab, Excel via openpyxl, CSV) | Done |
| 13 | User management (admin CRUD, activate/deactivate, change password) | Done |
| 14 | Diagrams, deployment guide, API reference | Done (see `docs/`) |

Webcam-based detection is also included: `/detection/webcam` captures a frame
client-side (browser `getUserMedia` + canvas) and runs it through the same
YOLOv8 pipeline as image upload.

> **Note on how this was built:** the code was written and statically
> verified (Python syntax checks, Jinja2 template parsing, and a full
> cross-check of every `url_for()` call against real route definitions) in a
> sandboxed environment with **no internet access and no MySQL server**, so
> YOLOv8/OpenCV inference and the database layer were never actually
> executed. Test the full pipeline — especially `detection/detector.py` with
> your own trained `best.pt` weights, and the MySQL schema — in your own
> environment before relying on it in production.

## Setup (Windows / Linux / VS Code)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/Mac
   venv\Scripts\activate         # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create the MySQL database**
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   This creates the `shelf_monitor` database, all tables, and seed data
   (3 sample shelves, 3 sample products, and an admin user).

   > Default login: **admin / admin123** — change it immediately after first
   > login via the "Change Password" link in the top navbar.

4. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env with your MySQL credentials if different from defaults
   ```

5. **Add your trained YOLOv8 model**

   Place your `best.pt` weights at `detection/best.pt` (or set
   `YOLO_MODEL_PATH` in `.env`). Every `Product.class_label` in the database
   must exactly match a class name the model was trained on so detections
   can be linked back to product records.

6. **Run the app**
   ```bash
   python run.py
   ```
   Visit `http://localhost:5000/auth/login`

## Alternative: let SQLAlchemy create the tables

Instead of `schema.sql`, you can also run:
```bash
flask --app run.py init-db
flask --app run.py create-admin
```

## Core workflows

- **Products** (`/products`) — CRUD with image upload, search, category filter.
- **Shelves** (`/shelves`) — CRUD plus a **planogram** per shelf: which
  products are expected there and in what quantity.
- **Detect (Upload)** (`/detection/upload`) — upload a shelf photo, run
  YOLOv8, get an annotated image + per-product counts.
- **Detect (Webcam)** (`/detection/webcam`) — capture a live frame and run
  the same pipeline.
- **Detection History** (`/detection/history`) — browse past scans, filter
  by shelf.
- **Dashboard** (`/dashboard`) — KPIs + Chart.js analytics (7-day scan
  trend, open-alert breakdown by type, most-scanned shelves).
- **Reports** (`/reports`) — generate PDF / Excel / CSV summaries of scans
  and alerts for a date range, optionally filtered by shelf.
- **Users** (`/users`, admin only) — create/edit/deactivate/delete users;
  any user can change their own password.

## How detection → alerts works

1. `detection/detector.py` runs YOLOv8 on the image and returns bounding
   boxes + class labels + confidences.
2. `app/utils/shelf_analysis.py`:
   - matches each detection's class label to a `Product` record,
   - computes **shelf coverage** (total detected box area ÷ image area) to
     decide if the shelf is empty (`EMPTY_SHELF_THRESHOLD` in `.env`),
   - counts detections per product and compares against the shelf's
     planogram, raising **low-stock** alerts when counts fall under a
     product's `min_stock_threshold`,
   - raises a **misplaced-product** alert if a recognized product is
     detected on a shelf that isn't part of its planogram.
3. Results are persisted as a `DetectionLog` + `DetectionItem` rows, and any
   alerts are saved to the `alerts` table, surfaced on the dashboard.

## Project structure

```
shelf-monitor/
├── app/
│   ├── models/         # SQLAlchemy models (User, Product, Shelf, DetectionLog, Alert...)
│   ├── routes/         # Blueprints (auth, dashboard, products, shelves, detection, reports, users)
│   ├── templates/      # Jinja2 + Bootstrap 5 templates
│   ├── static/         # CSS, JS, uploads, captures, generated reports
│   └── utils/          # shelf_analysis.py (Step 9-10 logic), report_generator.py (Step 12)
├── database/
│   └── schema.sql      # MySQL DDL + seed data
├── detection/
│   └── detector.py     # YOLOv8 wrapper (Step 7)
├── docs/
│   ├── er_diagram.md          # Mermaid ER diagram
│   ├── use_case_diagram.md    # Mermaid use-case diagram
│   ├── api_reference.md       # Full route reference
│   └── deployment.md          # Production deployment guide (Gunicorn + Nginx)
├── config.py
├── run.py
└── requirements.txt
```
