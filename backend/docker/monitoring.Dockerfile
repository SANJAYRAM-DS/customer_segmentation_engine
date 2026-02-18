# Monitoring Service Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies + monitoring tools
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir prometheus-client

# Copy application code
COPY backend/ ./backend/

# Create non-root user
RUN useradd -m -u 1000 monitoruser && \
    chown -R monitoruser:monitoruser /app
USER monitoruser

# Expose metrics port
EXPOSE 9090

# Default command (drift monitoring service)
CMD ["python", "-m", "backend.monitoring.drift_monitor"]
