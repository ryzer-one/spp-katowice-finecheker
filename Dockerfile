# Minimal Dockerfile for finechecker with Chromium + chromedriver
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      chromium chromium-driver fonts-liberation ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Create non-root user with writable home for caches
RUN useradd -m -d /home/appuser -U appuser
ENV HOME=/home/appuser \
    XDG_CACHE_HOME=/home/appuser/.cache \
    SELENIUM_MANAGER_CACHE=/home/appuser/.cache/selenium
RUN mkdir -p "$XDG_CACHE_HOME" && chown -R appuser:appuser /home/appuser

USER appuser

ENTRYPOINT ["finechecker"]
