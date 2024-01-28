#!/bin/bash

#region
white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'

# echo -e "${red}xxx${nc}"
nc='\033[0m'
#endregion

workdir=$(cd $(dirname $0); pwd)

if [ $(id -u) -ne 0 ]; then
    echo "run as root"
    exit 1
fi

if [ $(which docker 2>&1 > /dev/null; echo $?) -ne 0 ]; then
    echo "docker not found, or place it in /usr/bin/docker"
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "usage: $0 args"
    exit 1
fi

while read -r line; do
	echo $line
done < $(cat $1)

loop_file_list=(
	"file1"
	"file2"
	"file3"
)
for file in ${loop_file_list[@]}; do
	echo $file
done

for arg in "$@"; do
    if [ "$arg" = "--help" ]; then
        echo "show help menu"
        exit 0
    fi
done

case "$1" in
    start)
        echo "start"
        ;;
    stop)
        echo "stop"
        ;;
    restart)
        echo "restart"
        ;;
    *)
        echo "usage: $0 {enc|dec|show}"
esac

while getopts "uc3h" opt; do
	case ${opt} in
		u )
		info "update"
			apt-get update -y &> /dev/null

			if [ $? -eq 0 ]; then
				auto_update_success=1
			else
				auto_update_success=0
			fi

			if [ $auto_update_success -eq 1 ]; then
				info "update success"
			else
				fail "update failed"
			fi
			;;
		b )
        info "check"
			seperator
			info "check num: 1 - 10"
			read check_num
			while true
			do
				if ! [[ $check_num =~ ^[0-9]+$ ]]; then
					fail "input check_num"
					read check_num_result
				else
					break
				fi
			done

			read check_num_result
			while true
			do
				if ! [[ $check_num_result =~ ^[0-9]+$ ]] || [ $check_num_result -lt 1 ] || [ $check_num_result -gt 31 ] ; then
					read result
				else
					break
				fi
			done

            echo "check_num: $check_num"
            echo "check_num_result: $check_num_result"
            ;;
		3 )
		info "test"
            exit 0
			;;
		h )
			info "Usage: $0 [-u] [-b] [-3] [-h]"
			info "opt: "
            info "  -u: update"
            info "  -b: check"
            info "  -3: exit"
			exit 0
			;;
		\? )
			info "Invalid Option: -$OPTARG" 1>&2
			exit 1
			;;
	esac
done

find_genshin() {
    current_dir=$(pwd)
	if [ $# -eq 1 ]; then
		target_dir_name=$1
	else
		target_dir_name="genshin"
	fi

    while [[ "$current_dir" != "/" ]]; do
        base_name=$(basename "$current_dir")
        if [[ "$base_name" == "$target_dir_name" ]]; then
            return $current_dir
        fi
        current_dir=$(dirname "$current_dir")
    done

    echo -e "${RED}Error: $target_dir_name directory not found${nc}"
    return 1
}