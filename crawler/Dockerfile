FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (curl useful for health checks)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app ./app

# Environment variables (overridden in compose)
ENV CASSANDRA_HOST=cassandra
ENV ELASTICSEARCH_HOST=elasticsearch
ENV ES_INDEX=pages
ENV SERVICE_NAME=crawler

# Run the crawler
CMD ["python", "-m", "app.main"]
