FROM python:3.11-slim

WORKDIR /app

# Build context is the project root (.)
# so all paths below are relative to the project root.
COPY api/requirements.txt .
COPY api/main.py .
COPY api/templates ./templates

# Copy the services tree so the API can subprocess-call each service
# and so shared/ (registry + logger) is importable at /app/services/shared/
COPY services /app/services

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
