FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY repo/ .

RUN pip install --no-cache-dir -r requirements.txt

ENV CONFIG_PATH=/app/config/config.docker.yaml

EXPOSE 18080

CMD ["python", "run.py"]
