#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly ENV_FILE="$SCRIPT_DIR/.env"
readonly ENV_EXAMPLE_FILE="$SCRIPT_DIR/.env.example"
readonly CONFIG_DIR="$SCRIPT_DIR/config"

main() {
    mkdir -p -- "$CONFIG_DIR"
    chmod 700 "$CONFIG_DIR"

    if [[ ! -f "$ENV_FILE" && -f "$ENV_EXAMPLE_FILE" ]]; then
        cp -- "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    fi
}

main "$@"
