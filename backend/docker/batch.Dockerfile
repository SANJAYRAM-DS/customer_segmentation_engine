# Batch Inference Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/

# Create non-root user
RUN useradd -m -u 1000 batchuser && \
    chown -R batchuser:batchuser /app
USER batchuser

# Default command (can be overridden)
CMD ["python", "-m", "backend.orchestration.batch_inference"]
