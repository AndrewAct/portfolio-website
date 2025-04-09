# Builder stage
FROM python:3.11-alpine AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    g++

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# First uninstall bson if it exists
RUN pip uninstall -y bson

# Copy and install requirements first (for better caching)
COPY requirements.txt .

## Install MongoDB-related packages and requirements
#RUN pip install --no-cache-dir \
#    "pymongo[srv]==4.6.1" \
#    "motor==3.3.2" \
#    "pydantic>=2.5.2" \
#    "pydantic-settings>=2.1.0" \
#    -r requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-alpine

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install only required runtime dependencies
RUN apk add --no-cache libffi openssl

# Create non-root user
RUN adduser -D appuser

# Copy the .env file first
COPY .env .env

# Copy project files
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]