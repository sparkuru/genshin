#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(dirname -- "$0")
SCRIPT_DIR=$(cd -- "$script_dir" && pwd)
readonly SCRIPT_DIR
readonly EXTENSIONS_FILE="$SCRIPT_DIR/config/extensions.txt"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

main() {
	local codium_bin=${CODIUM_BIN:-codium}
	local extension_id
	local -a unavailable_extensions=()

	[[ -f "$EXTENSIONS_FILE" ]] || die "extension list not found: $EXTENSIONS_FILE"
	command -v "$codium_bin" >/dev/null 2>&1 || die "VSCodium command not found: $codium_bin"

	while IFS= read -r extension_id || [[ -n "$extension_id" ]]; do
		[[ -z "$extension_id" || "$extension_id" == \#* ]] && continue
		if ! "$codium_bin" --install-extension "$extension_id"; then
			unavailable_extensions+=("$extension_id")
		fi
	done <"$EXTENSIONS_FILE"

	if [[ ${#unavailable_extensions[@]} -gt 0 ]]; then
		printf 'Unavailable extensions:\n' >&2
		printf '  %s\n' "${unavailable_extensions[@]}" >&2
		return 1
	fi
}

main "$@"
