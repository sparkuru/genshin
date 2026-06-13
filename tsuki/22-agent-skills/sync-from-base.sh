#!/usr/bin/env bash
set -Eeuo pipefail

workdir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"

base_repo_path="$(cd "$workdir/../../../../" && pwd)"
geass_path="$base_repo_path/21-geass"
base_skill_path="$geass_path/skills"
target_dir="$workdir/base"

contains_name() {
	local wanted_name="$1"
	shift

	local name
	for name in "$@"; do
		[[ "$name" == "$wanted_name" ]] && return 0
	done
	return 1
}

clean_stale_links() {
	local target_dir="$1"
	shift

	local link name
	local had_nullglob=false
	shopt -q nullglob && had_nullglob=true
	shopt -s nullglob

	for link in "$target_dir"/*; do
		[ -L "$link" ] || continue

		name="$(basename "$link")"
		if ! contains_name "$name" "$@" || [ ! -e "$link" ]; then
			printf 'remove: %s\n' "$link"
			rm -f -- "$link"
		fi
	done

	"$had_nullglob" || shopt -u nullglob
}

mkdir -p -- "$target_dir"

skill_names=()
for d in "$base_skill_path"/*/; do
	[ -d "$d" ] || continue
	skill_names+=("$(basename "$d")")
done

clean_stale_links "$target_dir" "${skill_names[@]}"

for d in "$base_skill_path"/*/; do
	[ -d "$d" ] || continue
	ln -sfn "${d%/}" "$target_dir/$(basename "$d")"
done
