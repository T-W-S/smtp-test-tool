FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -U pip

# Install required packages
RUN pip install --no-cache-dir email-validator flask flask-sqlalchemy gunicorn \
    psycopg2-binary reportlab requests

# Copy application code
COPY . .

# Create data directory for configuration files and logs
RUN mkdir -p /data/config && \
    mkdir -p /data/logs && \
    chmod -R 777 /data

# Set environment variables
ENV SMTP_CONFIG_DIR=/data/config
ENV SMTP_LOG_DIR=/data/logs
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py

# Default port
EXPOSE 5000

# Add healthcheck to verify the application is running properly
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health_check || exit 1

# Run the application with production settings (single worker to prevent duplicates)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--workers=1", "--access-logfile=-", "--error-logfile=-", "main:app"]