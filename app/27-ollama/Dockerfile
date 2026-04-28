FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    OLLAMA_MODEL=nemotron-3-nano:latest \
    OLLAMA_TIMEOUT=600

WORKDIR /app

COPY cli/ /app/

RUN useradd --create-home --shell /bin/bash app \
    && chmod 755 /app/ollama_cli.py \
    && ln -s /app/ollama_cli.py /usr/local/bin/ollama-cli \
    && chown -R app:app /app

USER app
WORKDIR /workspace

ENTRYPOINT ["ollama-cli"]
