FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends squid curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY squid.conf /etc/squid/squid.conf
COPY lists/ /etc/squid/lists/
COPY entrypoint.sh /usr/local/bin/proxy-entrypoint.sh

# 非特権ユーザで起動し、PID は書き込み可能な場所に置く。
USER proxy
ENTRYPOINT ["sh", "/usr/local/bin/proxy-entrypoint.sh"]
CMD ["squid", "-N", "-f", "/etc/squid/squid.conf"]
