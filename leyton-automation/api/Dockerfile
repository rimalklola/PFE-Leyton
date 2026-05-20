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

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
