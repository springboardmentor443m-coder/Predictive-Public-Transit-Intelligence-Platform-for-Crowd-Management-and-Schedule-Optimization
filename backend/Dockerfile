# 1. Base Image: Lightweight Python 3.11 Debian slim
FROM python:3.11-slim

# Set environment variables: disable python bytecode generation and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system build dependencies for psycopg2 and numpy/scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Layer Caching: Copy requirements first so dependencies are cached
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and Alembic migrations
COPY . .

# Expose FastAPI service port
EXPOSE 8000

# Start Uvicorn ASGI server binding to 0.0.0.0 for container networking
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
