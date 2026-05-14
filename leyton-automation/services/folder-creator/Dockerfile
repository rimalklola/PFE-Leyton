FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY folder-creator/requirements.txt .
COPY folder-creator/main.py .
COPY folder-creator/mock_data.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
