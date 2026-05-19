#!/bin/bash

workdir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"

base_repo_path="$(cd "$workdir/../../../../" && pwd)"
geass_path="$base_repo_path/21-geass"
base_skill_path="$geass_path/skills"

for d in "$base_skill_path"/*/; do
	[ -d "$d" ] || continue
	ln -sfn "${d%/}" "$workdir/base/$(basename "$d")"
done