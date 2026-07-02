#!/usr/bin/env bash
# Derive include.yaml from himitsu/magic.yaml: strip proxies / proxy-groups
# and rewrite sensitive group names in the retained head and rules sections.
set -Eeuo pipefail

readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
readonly SRC_PATH="$SCRIPT_DIR/himitsu/magic.yaml"
readonly DST_PATH="$SCRIPT_DIR/include.yaml"

TMP_PATH=""

usage() {
    printf 'Usage: %s [--help]\n' "$SCRIPT_NAME" >&2
    printf '  Sanitize %s into %s\n' "$SRC_PATH" "$DST_PATH" >&2
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
    [[ -n "$TMP_PATH" && -f "$TMP_PATH" ]] && rm -f -- "$TMP_PATH"
}

render_yaml() {
    local src="$1"
    local dst="$2"

    python3 - "$src" "$dst" <<'PYEOF'
import re
import sys
from pathlib import Path

src_path = Path(sys.argv[1])
dst_path = Path(sys.argv[2])

NAME_MAP = {
    "tree-diagram": "outside",
    "schale":       "inside",
}

GENERIC_BLOCK = """proxies:
  - {
      name: "test",
      server: test.test.com,
      port: 1234,
      type: trojan,
      password: testpassword,
      sni: test.test.com,
      skip-cert-verify: true,
      udp: true,
    }
proxy-groups:
  - name: outside
    type: select
    proxies:
      - DIRECT
      - test
  - name: inside
    type: select
    proxies:
      - DIRECT
      - outside
      - reject
  - name: other
    type: select
    proxies:
      - DIRECT
      - outside
  - name: bilibili
    type: select
    proxies:
      - DIRECT
      - outside
      - inside
  - name: apple
    type: select
    proxies:
      - DIRECT
      - outside
      - inside
  - name: steam
    type: select
    proxies:
      - DIRECT
      - outside
      - inside
  - name: llm
    type: select
    proxies:
      - DIRECT
      - outside
      - test
  - name: reject
    type: select
    proxies:
      - outside
      - DIRECT
      - REJECT
"""

lines = src_path.read_text(encoding="utf-8").splitlines()


def find_top(name: str) -> int:
    for i, line in enumerate(lines):
        if line.startswith(f"{name}:"):
            return i
    return -1


idx_proxies = find_top("proxies")
idx_rules = find_top("rules")
if idx_proxies < 0 or idx_rules < 0 or idx_rules <= idx_proxies:
    sys.exit("magic.yaml missing required top-level sections: proxies / rules")

head = "\n".join(lines[:idx_proxies])
rules = "\n".join(lines[idx_rules:])


def remap(text: str) -> str:
    for key in sorted(NAME_MAP, key=len, reverse=True):
        pattern = rf"(?<![A-Za-z0-9_-]){re.escape(key)}(?![A-Za-z0-9_-])"
        text = re.sub(pattern, NAME_MAP[key], text)
    return text


out = remap(head) + "\n" + GENERIC_BLOCK + remap(rules) + "\n"
dst_path.write_text(out, encoding="utf-8")
PYEOF
}

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                usage
                return 0
                ;;
            --)
                shift
                break
                ;;
            -*)
                usage
                die "unknown option: $1"
                ;;
            *)
                usage
                die "unexpected argument: $1"
                ;;
        esac
    done

    [[ -f "$SRC_PATH" ]] || die "source file not found: $SRC_PATH"
    require_command python3

    TMP_PATH=$(mktemp "${TMPDIR:-/tmp}/include.XXXXXX.yaml")
    trap cleanup EXIT

    render_yaml "$SRC_PATH" "$TMP_PATH"
    mv -- "$TMP_PATH" "$DST_PATH"
    TMP_PATH=""

    printf 'wrote %s\n' "$DST_PATH"
}

main "$@"
