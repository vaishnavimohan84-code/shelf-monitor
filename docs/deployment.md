# Deployment Guide

## Local development (recap)
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
mysql -u root -p < database/schema.sql
cp .env.example .env            # edit with your MySQL credentials
python run.py
```
Visit `http://localhost:5000/auth/login` (default: `admin` / `admin123`).

## Adding your trained YOLOv8 model
1. Place your trained weights file at `detection/best.pt`
   (or point `YOLO_MODEL_PATH` in `.env` to wherever it lives).
2. Make sure each `Product.class_label` in the database exactly matches a
   class name the model was trained on — this is how detections are linked
   back to product records.
3. Tune `YOLO_CONF` (confidence threshold) and `EMPTY_SHELF_THRESHOLD`
   (fraction of shelf area that must be covered by detections before it's
   considered "stocked") in `.env` to match your camera setup and shelf
   layout.

## Production deployment (Linux server, e.g. Ubuntu + Nginx + Gunicorn)

1. **Install system packages**
   ```bash
   sudo apt update
   sudo apt install python3-venv python3-pip mysql-server nginx libgl1
   ```
   `libgl1` is required by OpenCV's `cv2` at runtime on headless servers.

2. **Set up the app**
   ```bash
   git clone <your-repo-url> shelf-monitor
   cd shelf-monitor
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   ```

3. **Configure environment** — create `.env` with production values:
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate a long random value>
   DB_HOST=localhost
   DB_USER=shelf_monitor_app
   DB_PASSWORD=<strong password>
   DB_NAME=shelf_monitor
   YOLO_MODEL_PATH=/opt/shelf-monitor/detection/best.pt
   ```

4. **Initialize the database**
   ```bash
   mysql -u root -p < database/schema.sql
   # or: flask --app run.py init-db && flask --app run.py create-admin
   ```

5. **Run with Gunicorn** (behind Nginx as a reverse proxy):
   ```bash
   gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app('production')"
   ```

6. **Nginx reverse proxy** (`/etc/nginx/sites-available/shelf-monitor`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       client_max_body_size 20M;  # allow shelf photo uploads

       location /static/ {
           alias /opt/shelf-monitor/app/static/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Run Gunicorn as a systemd service** so it restarts on boot/crash —
   create `/etc/systemd/system/shelf-monitor.service` pointing `ExecStart`
   at the Gunicorn command above, then `systemctl enable --now shelf-monitor`.

8. **HTTPS**: use `certbot --nginx` (Let's Encrypt) once the domain is
   pointed at the server.

## Notes on scaling detection workloads
- YOLOv8 inference is CPU/GPU-bound; a single Gunicorn worker holds one
  loaded model in memory (`detection/detector.py` uses a lazy-loaded
  singleton). For heavy traffic, consider a dedicated inference service
  or a task queue (Celery/RQ) instead of running inference inline in the
  request handler.
- Webcam capture happens client-side (browser `getUserMedia` + canvas);
  only the captured JPEG frame is POSTed to the server, so no extra
  server-side video-streaming infrastructure is needed.
