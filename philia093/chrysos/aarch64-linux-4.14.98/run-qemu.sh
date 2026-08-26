#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck disable=SC2034 # Profile metadata is consumed by the sourced common library.

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
profile_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly PROFILE_DIR="$profile_dir"
readonly PROFILE_NAME="aarch64-linux-4.14.98"
readonly BUILDROOT_VERSION="2024.05.3"
readonly QEMU_PORT="4546"
export SCRIPT_NAME PROFILE_DIR PROFILE_NAME BUILDROOT_VERSION QEMU_PORT

# shellcheck disable=SC1091 # The source path is intentionally relative to this profile.
source "$PROFILE_DIR/../buildroot-common.sh"

start_qemu_profile "${1:-}"
