FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr tesseract-ocr-chi-sim pandoc fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.lock /opt/dwmt/requirements.lock
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout 120 --retries 3 -r /opt/dwmt/requirements.lock
COPY scripts /opt/dwmt/scripts
COPY assets /opt/dwmt/assets
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/cache/huggingface
WORKDIR /work
ENTRYPOINT ["python", "/opt/dwmt/scripts/pipeline.py"]
