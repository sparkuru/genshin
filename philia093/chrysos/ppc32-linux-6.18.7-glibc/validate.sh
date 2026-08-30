#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
profile_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
readonly PROFILE_DIR="$profile_dir"
export SCRIPT_NAME

# shellcheck disable=SC1090,SC1091 # The profile owns this runtime path.
source "$PROFILE_DIR/profile.env"
# shellcheck disable=SC1091 # The profile owns this local lifecycle library.
source "$PROFILE_DIR/common.sh"

validate_profile "${1:-}"
