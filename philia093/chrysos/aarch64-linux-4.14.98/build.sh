#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck disable=SC2034 # Profile metadata is consumed by the sourced common library.

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
profile_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly PROFILE_DIR="$profile_dir"
readonly PROFILE_NAME="aarch64-linux-4.14.98"
readonly BUILDROOT_VERSION="2024.05.3"
readonly BUILDROOT_ARCHIVE="buildroot-$BUILDROOT_VERSION.tar.xz"
readonly BUILDROOT_URL="https://buildroot.org/downloads/$BUILDROOT_ARCHIVE"
readonly BUILDROOT_SHA256="b888ed7cb22cba1b5cbd242f9dcd31e090bd9c908d404f12f1b950e0062b6969"
readonly LINUX_VERSION="4.14.98"
readonly LINUX_ARCHIVE="linux-$LINUX_VERSION.tar.xz"
readonly LINUX_URL="https://cdn.kernel.org/pub/linux/kernel/v4.x/$LINUX_ARCHIVE"
readonly LINUX_SHA256="8f021171b1b1efb41326e603116a45126fc030d06aaa9b0784ae612323010c5f"
readonly LINUX_HEADERS_OPTION="BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_4_14"
readonly QEMU_PORT="4546"
readonly BUILDROOT_DEFCONFIG_TEMPLATE="$PROFILE_DIR/buildroot.defconfig.in"
export SCRIPT_NAME PROFILE_DIR PROFILE_NAME BUILDROOT_VERSION BUILDROOT_ARCHIVE \
	BUILDROOT_URL BUILDROOT_SHA256 LINUX_VERSION LINUX_ARCHIVE LINUX_URL LINUX_SHA256 \
	LINUX_HEADERS_OPTION \
	QEMU_PORT BUILDROOT_DEFCONFIG_TEMPLATE

# shellcheck disable=SC1091 # The source path is intentionally relative to this profile.
source "$PROFILE_DIR/../buildroot-common.sh"

build_profile "$@"
