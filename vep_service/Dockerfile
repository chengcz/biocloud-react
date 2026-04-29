# VEP Annotation Service Dockerfile
# Uses official Ensembl VEP image from Docker Hub
# https://hub.docker.com/r/ensemblorg/ensembl-vep

FROM ensemblorg/ensembl-vep:latest

# Install Python and dependencies
USER root

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Create working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code (flat structure - no app/ subdirectory)
COPY api/ ./api/
COPY models/ ./models/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY config/ ./config/
COPY main.py .
COPY species.yaml .

# Create directories for uploads and temp files
RUN mkdir -p /tmp/vep_service/uploads /data/vep_data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8001

# VEP data directory (mount this for reference data)
VOLUME ["/data/vep_data"]

# Expose port
EXPOSE 8001

# Run the application (flat structure: main:app, not app.main:app)
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]