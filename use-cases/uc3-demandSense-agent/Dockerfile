FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run injects PORT at runtime; default to 8080 for local testing
ENV PORT=8080

# Run with gunicorn: 1 worker, 8 threads, binds to Cloud Run's $PORT
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
