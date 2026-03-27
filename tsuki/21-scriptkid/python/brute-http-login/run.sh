#!/bin/bash

workdir=$(
	cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd
)

bp_file="${workdir}/bp.txt"
target_file="${workdir}/http-target.json"
script_file="${workdir}/brute-http-login.py"

user_file="/path/to/user.txt"
password_file="/path/to/password.txt"

python3 "${script_file}" \
	--raw-request-file "${bp_file}" \
	--target-file "${target_file}" \
	--users "${user_file}" \
	--passwords "${password_file}" \
	--threads 10 \
	--timeout-seconds 10 \
	--verify-tls \
	--pause-on-success \
	--log
