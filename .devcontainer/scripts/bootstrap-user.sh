#!/usr/bin/env bash
set -euo pipefail

zshrc_src="$(ls -d /workspaces/*/mtf/.zshrc 2>/dev/null | head -n 1 || true)"
if [[ -n "${zshrc_src}" && -f "${zshrc_src}" ]]; then
  cp -f "${zshrc_src}" "/home/vscode/.zshrc" || true
fi

chsh -s /usr/bin/zsh vscode || true

cat <<'EOF'
Installed tool versions:
EOF

python3 --version || true
node --version || true
go version || true
cargo --version || true
gcc --version | head -n 1 || true
php --version | head -n 1 || true
nginx -v || true
