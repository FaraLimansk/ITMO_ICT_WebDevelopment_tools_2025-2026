FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY worker/celery_app.py .
COPY worker/tasks.py .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]

