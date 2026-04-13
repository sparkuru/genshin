#!/usr/bin/env bash
set -euo pipefail

index=25
app_name=hot-news
compose_file=hot-news.yaml

# Tunables: edit then run ./init.sh (use --force to overwrite existing files).

create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
    fi
}

work_dir="$(cd -- "$(dirname -- "$0")" && pwd)"

MYSQL_ROOT_PASSWORD=newsroot	# change this
MYSQL_DATABASE=news_crawler
MYSQL_USER=news_app
MYSQL_PASSWORD=news_app_secret	# change this
API_PORT=18080

escape_yaml_double() {
    local s=$1
    s=${s//\\/\\\\}
    s=${s//\"/\\\"}
    printf '%s' "$s"
}

write_hot_news_yaml() {
    local rp dq du dp
    rp=$(escape_yaml_double "$MYSQL_ROOT_PASSWORD")
    dq=$(escape_yaml_double "$MYSQL_DATABASE")
    du=$(escape_yaml_double "$MYSQL_USER")
    dp=$(escape_yaml_double "$MYSQL_PASSWORD")
    cat >"$work_dir/$compose_file" <<EOF
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: "$rp"
      MYSQL_DATABASE: "$dq"
      MYSQL_USER: "$du"
      MYSQL_PASSWORD: "$dp"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./data/mysql/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "-u${MYSQL_USER}", "-p${MYSQL_PASSWORD}"]
      interval: 5s
      timeout: 5s
      retries: 15
      start_period: 30s
    networks:
      - hot_news_network

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - hot_news_network

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${API_PORT}:18080"
    environment:
      CONFIG_PATH: /app/config/config.docker.yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18080/health"]
      interval: 5s
      timeout: 3s
      retries: 5
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hot_news_network

volumes:
  mysql_data:

networks:
  hot_news_network:
    driver: bridge
EOF
}

write_dockerfile() {
    cat >"$work_dir/Dockerfile" <<'EOF'
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
EOF
}

write_config_docker_yaml() {
    local dq du dp
    dq=$(escape_yaml_double "$MYSQL_DATABASE")
    du=$(escape_yaml_double "$MYSQL_USER")
    dp=$(escape_yaml_double "$MYSQL_PASSWORD")
    create_dir "$work_dir/repo/config"
    cat >"$work_dir/repo/config/config.docker.yaml" <<EOF

app:
  title: "News Crawler API"
  description: "API for news crawling and management"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 18080
  debug: false
  cors:
    allow_origins: ["*"]
    allow_credentials: true
    allow_methods: ["*"]
    allow_headers: ["*"]

database:
  host: "mysql"
  user: "$du"
  password: "$dp"
  db: "$dq"
  charset: "utf8mb4"
  autocommit: true


redis:
  host: "redis"
  port: 6379
  db: 0
  password: ""
  decode_responses: false
  socket_timeout: 5
  socket_connect_timeout: 5
  health_check_interval: 30

crawler:
  interval: 1800
  timeout: 1700
  max_retry_count: 2
  max_instances: 2
  misfire_grace_time: 300

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  dir: "logs"
  file: "app.log"
  max_size: 10485760
  backup_count: 5
  daily_backup_count: 30
  timezone: "Asia/Shanghai"

notification:
  dingtalk:
    enabled: false
    webhook_url: ""
    secret: ""
    timeout: 10
    notify_success: false


scheduler:
  thread_pool_size: 20
  process_pool_size: 5
  coalesce: true
  max_instances: 2
  misfire_grace_time: 300
  timezone: "Asia/Shanghai"
EOF
}

main() {
    local force=0
    for a in "$@"; do
        if [ "$a" = "--force" ]; then
            force=1
        fi
    done

    create_dir "$work_dir/data/mysql/init"

    local need_write=0
    [ ! -f "$work_dir/$compose_file" ] && need_write=1
    [ ! -f "$work_dir/Dockerfile" ] && need_write=1
    [ ! -f "$work_dir/repo/config/config.docker.yaml" ] && need_write=1
    [ "$force" -eq 1 ] && need_write=1

    if [ "$need_write" -eq 0 ]; then
        echo "skip: $compose_file, Dockerfile, repo/config/config.docker.yaml already exist (use --force to overwrite)"
        return 0
    fi

    write_hot_news_yaml
    write_dockerfile
    write_config_docker_yaml
    echo "[$index-$app_name] wrote $compose_file, Dockerfile, repo/config/config.docker.yaml"
    echo "mysql: database=$MYSQL_DATABASE user=$MYSQL_USER (app user, not root); MYSQL_ROOT_PASSWORD is for admin only"
}

main "$@"
