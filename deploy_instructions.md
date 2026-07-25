# Deployment Instructions

This repository is a Flask app and cannot be fully deployed on Netlify as a server-side application.

## Recommended Hosts

- Render
- Railway
- Heroku
- Fly.io
- Cloud Run / App Engine

## Docker Deployment

1. Build the container:
   ```bash
   docker build -t shelf-monitor .
   ```

2. Run locally:
   ```bash
   docker run -p 8080:8080 \
     -e DB_USE_SQLITE=true \
     -e SECRET_KEY=change-me \
     shelf-monitor
   ```

3. For a database-backed deployment, set these environment variables:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`
   - `YOLO_MODEL_PATH`
   - `SECRET_KEY`

## Netlify Note

Netlify can only host static files. This repository includes server logic, database access, and YOLO model inference, so the correct deployment is a containerized or server host.
