FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY pdf-timesheet-extractor/requirements.txt .
COPY pdf-timesheet-extractor/main.py .
COPY pdf-timesheet-extractor/mock_data.py .
COPY pdf-timesheet-extractor/generate_fixture.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
