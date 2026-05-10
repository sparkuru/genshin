FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends iptables iproute2 \
 && rm -rf /var/lib/apt/lists/* \
 && update-alternatives --set iptables /usr/sbin/iptables-legacy \
 && update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

COPY apply.sh /apply.sh
RUN chmod +x /apply.sh

ENTRYPOINT ["/apply.sh"]
