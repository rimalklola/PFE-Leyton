FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY timesheet-consolidator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY timesheet-consolidator/main.py .

# Security: run as non-root user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
