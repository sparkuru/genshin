#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck disable=SC2034 # Profile metadata is consumed by the sourced common library.

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
profile_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly PROFILE_DIR="$profile_dir"
readonly PROFILE_NAME="aarch64-linux-6.18.7"
readonly BUILDROOT_VERSION="2026.05.2"
readonly BUILDROOT_ARCHIVE="buildroot-$BUILDROOT_VERSION.tar.xz"
readonly BUILDROOT_URL="https://buildroot.org/downloads/$BUILDROOT_ARCHIVE"
readonly BUILDROOT_SHA256="7cd0b79e657b8a1760cef0a68d083265726efe96a17f7f0cb9c10dd6d29b7107"
readonly LINUX_VERSION="6.18.7"
readonly LINUX_ARCHIVE="linux-$LINUX_VERSION.tar.xz"
readonly LINUX_URL="https://cdn.kernel.org/pub/linux/kernel/v6.x/$LINUX_ARCHIVE"
readonly LINUX_SHA256="b726a4d15cf9ae06219b56d87820776e34d89fbc137e55fb54a9b9c3015b8f1e"
readonly LINUX_HEADERS_OPTION="BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_6_18"
readonly QEMU_PORT="4547"
readonly BUILDROOT_DEFCONFIG_TEMPLATE="$PROFILE_DIR/buildroot.defconfig.in"
export SCRIPT_NAME PROFILE_DIR PROFILE_NAME BUILDROOT_VERSION BUILDROOT_ARCHIVE \
	BUILDROOT_URL BUILDROOT_SHA256 LINUX_VERSION LINUX_ARCHIVE LINUX_URL LINUX_SHA256 \
	LINUX_HEADERS_OPTION \
	QEMU_PORT BUILDROOT_DEFCONFIG_TEMPLATE

# shellcheck disable=SC1091 # The source path is intentionally relative to this profile.
source "$PROFILE_DIR/../buildroot-common.sh"

build_profile "$@"
