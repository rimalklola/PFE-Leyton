FROM python:3.11-slim

WORKDIR /app

# shared/ must come first -- services import from shared.registry and shared.logger
COPY shared/ ./shared/

COPY client-onboarding-generator/requirements.txt .
COPY client-onboarding-generator/main.py .
COPY client-onboarding-generator/mock_data.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
