FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt email-validator

COPY . .

# Train initial baseline ML models inside docker build step
RUN PYTHONPATH=. python app/ml/train_demand_model.py
RUN PYTHONPATH=. python app/ml/train_crowd_model.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
