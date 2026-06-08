FROM python:3.11-slim

WORKDIR /app

# Build context is the project root (.)
COPY api/requirements.txt .
COPY api/main.py .
COPY api/templates ./templates

# Copy services tree so the API can subprocess-call each service.
# shared/ lives at /app/services/shared/ — add to PYTHONPATH so
# "from shared.registry import ..." works regardless of __file__ depth.
COPY services /app/services
ENV PYTHONPATH=/app/services
ENV SERVICES_ROOT=/app/services

RUN pip install --no-cache-dir -r requirements.txt

# Security: run as non-root user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
