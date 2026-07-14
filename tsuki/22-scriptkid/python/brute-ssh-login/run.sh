#!/bin/bash

workdir=$(
	cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd
)

target_file="${workdir}/ssh-target.json"
script_file="${workdir}/brute-ssh-login.py"

user_file="/path/to/user.txt"
password_file="/path/to/password.txt"

python3 "${script_file}" \
	--target-file "${target_file}" \
	--users "${user_file}" \
	--passwords "${password_file}" \
	--threads 5 \
	--timeout-seconds 15 \
	--pause-on-success \
	--log
