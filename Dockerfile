FROM python:3.9-slim

WORKDIR /app


COPY requirements.txt .

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

CMD ["gunicorn", "--workers=3", "--max-requests=100", "--max-requests-jitter=10", "--timeout=600", "app:app"]

EXPOSE 8000
