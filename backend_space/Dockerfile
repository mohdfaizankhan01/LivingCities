FROM python:3.12-slim

WORKDIR /app

# Cache/writable dirs — HF Spaces runs as a non-root user
ENV HOME=/app \
    PYTHONUNBUFFERED=1 \
    COGNEE_SYSTEM_DIRECTORY=/app/.cognee_system \
    COGNEE_DATA_DIRECTORY=/app/.cognee_data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Spaces expects the app on port 7860
EXPOSE 7860
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
