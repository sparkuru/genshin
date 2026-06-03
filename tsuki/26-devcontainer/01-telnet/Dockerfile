FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash coreutils procps iproute2 passwd net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY --from=busybox:musl /bin/busybox /bin/busybox-full
RUN chmod +x /bin/busybox-full \
    && ln -sf /bin/busybox-full /bin/telnetd \
    && ln -sf /bin/busybox-full /bin/login

WORKDIR /app

COPY config/ /app/config/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 23/tcp

ENTRYPOINT ["/app/entrypoint.sh"]