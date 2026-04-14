# syntax=docker/dockerfile:1.7

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG KOHARU_VERSION=latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fonts-noto-cjk \
        libayatana-appindicator3-1 \
        libgomp1 \
        librsvg2-2 \
        libssl3 \
        libwebkit2gtk-4.1-0 \
        libxdo3 \
    && if [ "$KOHARU_VERSION" = "latest" ]; then \
        curl -fL "https://github.com/mayocream/koharu/releases/latest/download/koharu_linux_x64" -o /usr/local/bin/koharu; \
    else \
        curl -fL "https://github.com/mayocream/koharu/releases/download/${KOHARU_VERSION}/koharu_linux_x64" -o /usr/local/bin/koharu; \
    fi \
    && chmod 0755 /usr/local/bin/koharu \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash koharu \
    && install -d -o koharu -g koharu -m 755 /home/koharu/.local/share/Koharu

USER koharu
WORKDIR /home/koharu

VOLUME ["/home/koharu/.local/share/Koharu"]
EXPOSE 4000

ENTRYPOINT ["/usr/local/bin/koharu"]
CMD ["--headless", "--no-keyring", "--host", "0.0.0.0", "--port", "4000"]
