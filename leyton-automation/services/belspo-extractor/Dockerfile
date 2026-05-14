FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY belspo-extractor/requirements.txt .
COPY belspo-extractor/main.py .
COPY belspo-extractor/mock_data.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
