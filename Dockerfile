FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif1 libheif-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src
COPY web /app/web
COPY config.yml.example /app/config.yml.example

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "server"]