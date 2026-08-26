FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        iproute2 \
        iptables \
        kmod \
        tini \
        wireguard-tools \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/sbin/overlap-vpn-wireguard-entrypoint

RUN chmod 0755 /usr/local/sbin/overlap-vpn-wireguard-entrypoint

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/sbin/overlap-vpn-wireguard-entrypoint"]
