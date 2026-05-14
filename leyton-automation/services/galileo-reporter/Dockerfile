FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY galileo-reporter/requirements.txt .
COPY galileo-reporter/main.py .
COPY galileo-reporter/mock_data.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
