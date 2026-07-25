FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p app/static/uploads app/static/captures app/static/reports

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "run:app"]
