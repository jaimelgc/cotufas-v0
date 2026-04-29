FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files at build time (prod image)
# ARG so it's only used when building for prod
ARG COLLECT_STATIC=false
RUN if [ "$COLLECT_STATIC" = "true" ]; then \
    python manage.py collectstatic --noinput; fi

EXPOSE 8000
CMD ["gunicorn", "cotufas.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]