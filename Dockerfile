FROM python:3.12-slim

# ── system deps: Tesseract + language packs + libGL for OpenCV ──────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-por \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python deps (cached layer) ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── application code ─────────────────────────────────────────────────────────
COPY main.py .

# Volumes are declared here for documentation; actual mounts come from compose
VOLUME ["/app/input", "/app/output"]

CMD ["python", "main.py"]
