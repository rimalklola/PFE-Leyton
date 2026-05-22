FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY handover-generator/requirements.txt .
COPY handover-generator/main.py .
COPY handover-generator/mock_data.py .

RUN pip install --no-cache-dir -r requirements.txt

# Security: run as non-root user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
