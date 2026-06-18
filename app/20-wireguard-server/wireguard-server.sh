#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly COMPOSE_FILE="$SCRIPT_DIR/wireguard-server.yml"
readonly CONFIG_DIR="$SCRIPT_DIR/config"
readonly ENV_FILE="$SCRIPT_DIR/.env"

container_name() {
    if [[ -f "$ENV_FILE" ]]; then
        local value
        value=$(grep -E '^CONTAINER_NAME=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)
        [[ -n "$value" ]] && {
            printf '%s\n' "$value"
            return 0
        }
    fi

    printf 'wireguard\n'
}

compose() {
    if docker compose version >/dev/null 2>&1; then
        if [[ -f "$ENV_FILE" ]]; then
            docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
        else
            docker compose -f "$COMPOSE_FILE" "$@"
        fi
        return 0
    fi

    if [[ -f "$ENV_FILE" ]]; then
        docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
    else
        docker-compose -f "$COMPOSE_FILE" "$@"
    fi
}

peer_conf_path() {
    local peer_name=$1
    local literal_path="$CONFIG_DIR/${peer_name}/${peer_name}.conf"
    local named_path="$CONFIG_DIR/peer_${peer_name}/peer_${peer_name}.conf"
    local numeric_path="$CONFIG_DIR/peer${peer_name}/peer${peer_name}.conf"

    if [[ -f "$literal_path" ]]; then
        printf '%s\n' "$literal_path"
        return 0
    fi

    if [[ -f "$named_path" ]]; then
        printf '%s\n' "$named_path"
        return 0
    fi

    if [[ -f "$numeric_path" ]]; then
        printf '%s\n' "$numeric_path"
        return 0
    fi

    return 1
}

usage() {
    cat <<EOF
WireGuard Server Management

Usage: $SCRIPT_NAME {up|down|restart|status|logs|list|qr|conf} [peer]

Commands:
  up             Start the server
  down           Stop the server
  restart        Restart the server
  status         Show container status
  logs           Follow container logs
  list           List generated peers
  qr <peer>      Show QR code for a peer
  conf <peer>    Show peer config
EOF
}

require_peer() {
    [[ $# -gt 0 && -n "${1:-}" ]] || {
        usage >&2
        exit 2
    }
}

show_peer_qr() {
    local peer_name=$1
    docker exec -it "$(container_name)" /app/show-peer "$peer_name"
}

list_peers() {
    [[ -d "$CONFIG_DIR" ]] || return 0

    find "$CONFIG_DIR" -maxdepth 1 -type d \( -name 'peer*' -o -name 'peer_*' \) -printf '%f\n' | sort
}

show_peer_conf() {
    local peer_name=$1
    local peer_conf

    if ! peer_conf=$(peer_conf_path "$peer_name"); then
        printf 'Error: peer config not found for %s\n' "$peer_name" >&2
        exit 1
    fi

    cat "$peer_conf"
}

restart_container() {
    compose restart
}

show_logs() {
    compose logs -f
}

show_status() {
    compose ps
}

main() {
    local command=${1:-}

    case "$command" in
    up)
        compose up -d
        ;;
    down)
        compose down
        ;;
    qr)
        shift
        require_peer "$@"
        show_peer_qr "$1"
        ;;
    list)
        list_peers
        ;;
    conf)
        shift
        require_peer "$@"
        show_peer_conf "$1"
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    -h | --help | help | "")
        usage
        ;;
    *)
        usage >&2
        exit 2
        ;;
    esac
}

main "$@"
