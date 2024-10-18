FROM python:3.9-slim

WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["gunicorn", "--workers=2", "--max-requests=100", "--max-requests-jitter=10", "--timeout=300", "app:app"]


EXPOSE 8000
