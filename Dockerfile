FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate

RUN python manage.py populate_districts
RUN python manage.py populate_db

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]