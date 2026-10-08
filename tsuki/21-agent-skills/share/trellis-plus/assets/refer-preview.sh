#!/usr/bin/env bash
# Source from a project-owned adapter; strict mode belongs to the executable caller.

readonly STYLE_PREVIEW_RESET=$'\033[0m'
readonly STYLE_PREVIEW_TITLE=$'\033[1;36m'
readonly STYLE_PREVIEW_SECTION=$'\033[1;32m'
readonly STYLE_PREVIEW_EXAMPLE=$'\033[0;37m'
readonly STYLE_PREVIEW_LOG=$'\033[0;36m'
readonly STYLE_PREVIEW_SUCCESS=$'\033[0;32m'
readonly STYLE_PREVIEW_WARNING=$'\033[1;33m'
readonly STYLE_PREVIEW_ERROR=$'\033[1;31m'

_preview_print() {
	local style=$1
	local output_fd=$2
	local message=$3

	if [[ -z ${NO_COLOR:-} && ${TERM:-} != dumb && -t $output_fd ]]; then
		printf '%s%s%s\n' "$style" "$message" "$STYLE_PREVIEW_RESET" >&"$output_fd"
	else
		printf '%s\n' "$message" >&"$output_fd"
	fi
}

preview_log() {
	_preview_print "$STYLE_PREVIEW_LOG" 2 "[log] $*"
}

preview_warn() {
	_preview_print "$STYLE_PREVIEW_WARNING" 2 "[warn] $*"
}

preview_error() {
	_preview_print "$STYLE_PREVIEW_ERROR" 2 "[error] $*"
}

preview_require_command() {
	command -v "$1" >/dev/null 2>&1 && return 0
	preview_error "Required command not found: $1"
	return 1
}

preview_script_root() {
	local script_path=$1
	local script_dir=.

	[[ $script_path != */* ]] || script_dir=${script_path%/*}
	(cd -- "$script_dir" && pwd -P)
}

preview_require_env_file() {
	local repo_root=$1

	[[ -f "$repo_root/.env" ]] && return 0
	preview_error "Missing $repo_root/.env. From the repository root, copy .env.example to .env and edit required values."
	return 1
}

preview_usage() {
	local program=${preview_program:-./preview.sh}
	local example

	_preview_print "$STYLE_PREVIEW_TITLE" 2 "Usage: $program [start|stop|down|status|build] [--verbose]"
	_preview_print "$STYLE_PREVIEW_SECTION" 2 'Commands:'
	printf '%s\n' \
		'  start       Prepare missing resources, start in background, wait for readiness.' \
		'              Default action; reuse healthy services with matching configuration.' \
		'  stop        Stop only owned preview services; preserve persistent data.' \
		'  down        Data-preserving alias for stop.' \
		'  status      Inspect actual state/health; never prepare or start services.' \
		'  build       Explicit image rebuild; never start services.' >&2
	_preview_print "$STYLE_PREVIEW_SECTION" 2 'Options:'
	_preview_print "$STYLE_PREVIEW_LOG" 2 '  --verbose   Request redacted detailed logs from the project lifecycle.'
	_preview_print "$STYLE_PREVIEW_LOG" 2 '  -h, --help  Show this help without loading configuration or calling the lifecycle.'
	_preview_print "$STYLE_PREVIEW_SECTION" 2 'First use:'
	printf '  %s\n' "${preview_help_setup:-Copy .env.example to .env only if absent; edit required keys; run ./preview.sh.}" >&2
	printf '  Required tools/values: %s\n' "${preview_help_requirements:-See the project development spec and .env.example.}" >&2
	printf '  Lifecycle/configuration: %s\n' "${preview_help_runtime:-Project adapter; see the development spec for loading order and rebuild rules.}" >&2
	printf '%s\n' \
		'  First preparation may download images/packages and take several minutes.' \
		'  Existing resources are reused; startup never runs tests automatically.' \
		'  Explicit offline/no-install and network constraints remain in effect.' \
		'  Success URLs describe runtime endpoints; cross-device access needs verification.' \
		'  The reference presentation helpers require Bash 4.4 or newer.' \
		'  Logs go to stderr; access summaries go to stdout. NO_COLOR disables ANSI color.' >&2
	_preview_print "$STYLE_PREVIEW_SECTION" 2 'Examples:'
	for example in "$program" "$program start --verbose" "$program status" "$program stop"; do
		_preview_print "$STYLE_PREVIEW_EXAMPLE" 2 "  $example"
	done
}

preview_main() {
	local action=start
	local action_seen=false
	local hook

	preview_verbose=false
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-h | --help)
			preview_usage
			return 0
			;;
		--verbose)
			# shellcheck disable=SC2034 # Consumed by project adapter functions.
			preview_verbose=true
			;;
		start | stop | down | status | build)
			if [[ $action_seen == true ]]; then
				preview_error 'Specify exactly one command.'
				return 2
			fi
			action=$1
			action_seen=true
			;;
		*)
			preview_error "Unknown argument: $1"
			preview_usage
			return 2
			;;
		esac
		shift
	done

	[[ $action != down ]] || action=stop
	hook="project_preview_$action"
	if ! declare -F "$hook" >/dev/null; then
		preview_error "Project adapter must define $hook; no lifecycle operation was performed."
		return 1
	fi
	# Preserve strict-mode behavior inside the lifecycle; do not wrap it in an if/! test.
	"$hook"
}

preview_summary_reset() {
	preview_summary_ready=false
	preview_url_sections=()
	preview_url_labels=()
	preview_url_services=()
	preview_url_values=()
	preview_listener_lines=()
	preview_published_lines=()
	preview_internal_lines=()
	preview_note_lines=()
}

preview_add_url() {
	local section=$1
	local label=$2
	local service=$3
	local url=$4
	local index
	local authority
	local host

	if [[ $section != open && $section != local ]]; then
		preview_error 'URL section must be open or local.'
		return 2
	fi
	if [[ ! $url =~ ^https?://[^[:space:]]+$ || $url == *'@'* ]]; then
		preview_error 'Browser URLs must use HTTP(S) without whitespace or credentials.'
		return 2
	fi
	authority=${url#*://}
	authority=${authority%%/*}
	if [[ $authority == \[* ]]; then
		host=${authority%%\]*}
		host="${host}]"
	else
		host=${authority%%:*}
	fi
	case "$host" in
	0.0.0.0 | '[::]')
		preview_error 'Wildcard addresses are not browser destinations.'
		return 2
		;;
	127.* | localhost | '[::1]')
		if [[ $section != local ]]; then
			preview_error 'Loopback URLs belong in Local only.'
			return 2
		fi
		;;
	esac
	if [[ -z $label || -z $service || $label == *$'\n'* || $service == *$'\n'* ]]; then
		preview_error 'Entry label and service must be nonempty single-line values.'
		return 2
	fi
	for ((index = 0; index < ${#preview_url_values[@]}; index++)); do
		if [[ ${preview_url_sections[index]} == "$section" && ${preview_url_labels[index]} == "$label" &&
			${preview_url_services[index]} == "$service" && ${preview_url_values[index]} == "$url" ]]; then
			return 0
		fi
	done
	preview_url_sections+=("$section")
	preview_url_labels+=("$label")
	preview_url_services+=("$service")
	preview_url_values+=("$url")
}

preview_add_line() {
	local section=$1
	local line=$2

	if [[ -z $line || $line == *$'\n'* ]]; then
		preview_error 'Summary lines must be nonempty single-line values.'
		return 2
	fi
	case "$section" in
	listeners) preview_listener_lines+=("$line") ;;
	published) preview_published_lines+=("$line") ;;
	internal) preview_internal_lines+=("$line") ;;
	notes) preview_note_lines+=("$line") ;;
	*)
		preview_error "Unknown summary section: $section"
		return 2
		;;
	esac
}

_preview_render_service_urls() {
	local section=$1
	local service=$2
	local index
	local other
	local -a seen_labels=()

	for ((index = 0; index < ${#preview_url_values[@]}; index++)); do
		[[ ${preview_url_sections[index]} == "$section" && ${preview_url_services[index]} == "$service" ]] || continue
		for ((other = 0; other < ${#seen_labels[@]}; other++)); do
			if [[ ${seen_labels[other]} == "${preview_url_labels[index]}" ]]; then
				break
			fi
		done
		[[ $other == "${#seen_labels[@]}" ]] || continue
		seen_labels+=("${preview_url_labels[index]}")
		printf '%s (%s):\n' "${preview_url_labels[index]}" "${preview_url_services[index]}"
		for ((other = index; other < ${#preview_url_values[@]}; other++)); do
			if [[ ${preview_url_sections[other]} == "$section" && ${preview_url_labels[other]} == "${preview_url_labels[index]}" &&
				${preview_url_services[other]} == "${preview_url_services[index]}" ]]; then
				printf '%s\n' "${preview_url_values[other]}"
			fi
		done
	done
}

_preview_render_urls() {
	local section=$1
	local heading=$2
	local index
	local other
	local -a seen_services=()

	for ((index = 0; index < ${#preview_url_values[@]}; index++)); do
		[[ ${preview_url_sections[index]} == "$section" ]] || continue
		for ((other = 0; other < ${#seen_services[@]}; other++)); do
			[[ ${seen_services[other]} != "${preview_url_services[index]}" ]] || break
		done
		[[ $other == "${#seen_services[@]}" ]] || continue
		if [[ ${#seen_services[@]} == 0 ]]; then
			printf '\n'
			_preview_print "$STYLE_PREVIEW_SECTION" 1 "$heading"
		fi
		seen_services+=("${preview_url_services[index]}")
		_preview_render_service_urls "$section" "${preview_url_services[index]}"
	done
}

_preview_render_lines() {
	local heading=$1
	shift
	[[ $# -gt 0 ]] || return 0
	printf '\n'
	_preview_print "$STYLE_PREVIEW_SECTION" 1 "$heading"
	printf '%s\n' "$@"
}

preview_render_summary() {
	if [[ ${preview_summary_ready:-false} != true ]]; then
		preview_error 'Every required service must pass readiness before rendering a success summary.'
		return 1
	fi
	if [[ ${#preview_listener_lines[@]} == 0 ]]; then
		preview_error 'A ready preview must report its actual service listeners.'
		return 1
	fi
	_preview_print "$STYLE_PREVIEW_SUCCESS" 1 'System is ready.'
	_preview_render_urls open 'Open:'
	_preview_render_urls local 'Local only (preview host):'
	_preview_render_lines 'Listeners:' "${preview_listener_lines[@]}"
	_preview_render_lines 'Published:' "${preview_published_lines[@]}"
	_preview_render_lines 'Internal only:' "${preview_internal_lines[@]}"
	_preview_render_lines 'Notes:' "${preview_note_lines[@]}"
}

_preview_reference_main() {
	if [[ $# -gt 1 ]]; then
		preview_error 'Reference accepts exactly one option: --help or --demo.'
		return 2
	fi
	case "${1:---help}" in
	-h | --help)
		preview_usage
		printf '\n%s\n' 'Reference only: --demo renders documentation fixtures; source this file from a project adapter.' >&2
		;;
	--demo)
		preview_log 'Demo fixtures only; no services were started or probed.'
		preview_summary_reset
		preview_add_url open Website web http://192.0.2.10:7081
		preview_add_url local Website web http://127.0.0.1:7081
		preview_add_line listeners 'Listening web: 0.0.0.0:80 (container; HTTP)'
		preview_add_line published 'Published web: 0.0.0.0:7081 -> 0.0.0.0:80 (active listener)'
		preview_add_line notes 'Demo fixtures; reachability was not tested.'
		preview_summary_ready=true
		preview_render_summary
		;;
	*)
		preview_error 'Reference supports only --help or --demo; use a project adapter for lifecycle commands.'
		return 2
		;;
	esac
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
	set -Eeuo pipefail
	_preview_reference_main "$@"
fi
