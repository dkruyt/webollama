FROM python:3.13-slim

WORKDIR /app

# Upgrade pip to latest to reduce supply-chain risk
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies before copying app code (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user before copying files so ownership is correct
RUN useradd -m appuser

# Copy application code (ensure .dockerignore excludes .env, .git, etc.)
COPY --chown=appuser:appuser . .

USER appuser

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5000

# Health check so Docker/orchestrators can detect crashes
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"

# Start the application
CMD ["python", "app.py"]
