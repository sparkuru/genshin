#!/usr/bin/env zsh

set -eu

app_name=openwebui
work_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
file_path="$work_dir/$app_name.yml"
env_path="$work_dir/.env"
data_dir="$work_dir/data"

mkdir -p "$data_dir"

if [ ! -f "$file_path" ]; then
    cat >"$file_path" <<'EOF'
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    environment:
      UID: "${UID}"
      GID: "${GID}"
      TZ: "${OPENWEBUI_TZ}"
      WEBUI_SECRET_KEY: "${WEBUI_SECRET_KEY}"
      ENABLE_OLLAMA_API: "${ENABLE_OLLAMA_API}"
      OLLAMA_BASE_URL: "${OLLAMA_BASE_URL}"
      RAG_OLLAMA_BASE_URL: "${RAG_OLLAMA_BASE_URL}"
    volumes:
      - ./data:/app/backend/data
    ports:
      - "${OPENWEBUI_PORT}:8080"
    restart: unless-stopped
EOF
fi

if [ ! -f "$env_path" ]; then
    cat >"$env_path" <<'EOF'
UID=1000
GID=1000
OPENWEBUI_TZ=Asia/Singapore
WEBUI_SECRET_KEY=change-me
ENABLE_OLLAMA_API=true
OLLAMA_BASE_URL=http://10.42.1.81:11434
RAG_OLLAMA_BASE_URL=http://10.42.1.81:11434
OPENWEBUI_PORT=8080
EOF
fi

printf 'compose file ready: %s\n' "$file_path"
printf '.env file ready: %s\n' "$env_path"
