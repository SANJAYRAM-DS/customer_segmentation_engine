# Use Python 3.10 slim as the base image
FROM python:3.10-slim

# Create a non-root user required by Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY --chown=user requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container
# This includes your models and parquet files!
COPY --chown=user backend/ ./backend/

# Hugging Face Spaces MUST run on port 7860
EXPOSE 7860

# Run the FastAPI application on port 7860
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "7860"]
