# ---- Stage 1: Build dependencies ----
FROM python:3.13.5-alpine3.22 AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies needed by common C-extension packages (e.g. aiohttp, cryptography)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    build-base \
    python3-dev

# Copy Python requirements and install with preferred binary wheels
COPY requirements.txt .

RUN pip install --upgrade --no-cache-dir --root-user-action=ignore pip setuptools wheel && \
    pip install --no-cache-dir --root-user-action=ignore --prefer-binary -r requirements.txt

# ---- Stage 2: Runtime image ----
FROM python:3.13.5-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN adduser -D appuser

# Install only the necessary runtime libraries
RUN apk add --no-cache \
    libffi \
    openssl

WORKDIR /app

# Copy Python packages and CLI tools from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy your bot source code and give ownership to the non-root user
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Start the bot
CMD ["python", "main.py"]
