# ── Stage: production image ──────────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install OS deps required by psycopg2 (libpq) and bcrypt (compiler headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer cache efficiency)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port uvicorn will bind to
EXPOSE 8000

# Production start command:
# - No --reload (file watching is for dev only)
# - Bind to 0.0.0.0 so Docker can route traffic in
# - Single worker per container; scale by running multiple containers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
