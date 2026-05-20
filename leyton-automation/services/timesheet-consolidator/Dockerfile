FROM python:3.11-slim
WORKDIR /app
COPY shared/ ./shared/
COPY timesheet-consolidator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY timesheet-consolidator/main.py .
CMD ["python", "main.py"]
