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

# IMPORTANT for Hugging Face Docker Spaces:
# We must use huggingface-cli to download the actual large binary files.
# First, we delete the LFS pointer files that were copied over so they don't block the download
RUN find backend/ -type f \( -name "*.parquet" -o -name "*.joblib" \) -delete
RUN pip install huggingface_hub
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Sanjayramdata/customersegmentation', repo_type='space', local_dir='/app', allow_patterns=['*.parquet', '*.joblib'], local_dir_use_symlinks=False)"

# Hugging Face Spaces MUST run on port 7860
EXPOSE 7860

# Run the FastAPI application on port 7860
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "7860"]
