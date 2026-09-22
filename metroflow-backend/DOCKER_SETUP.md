version: '3.8'

services:
  metroflow:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - metroflow_data:/app/data
      - /app/metroflow_xgboost_model.json
      - /app/AI_MetroFlow_Master_Dataset.xlsx
    environment:
      - PYTHONUNBUFFERED=1
      - PORT=8000
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"

volumes:
  metroflow_data:

# Build and run:
#   docker-compose up -d --build
# Stop:
#   docker-compose down
# View logs:
#   docker-compose logs -f backend
# Enter container:
#   docker-compose exec backend bash
