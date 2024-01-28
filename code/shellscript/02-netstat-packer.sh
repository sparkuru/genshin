#!/bin/sh

workdir="$(cd $(dirname $0); pwd)/netstat"
root_tar_dir_name="$(hostname)-$(date +%m%d-%H%M)"
root_tar_dir_path="$workdir/$root_tar_dir_name"
root_tar_file_name="$root_tar_dir_name.tar"

runtime_info_file_name="proc.log"
proc_file_path="$workdir/$runtime_info_file_name"

mkdir -p $root_tar_dir_path

get_runtime_info() {
    local pid=$1
    local split_line_symbol="\n----------------------------------------\n"

    echo -e "[$pid] proc info: $split_line_symbol" > "$proc_file_path"

    redirect_output() {
        echo "$USER@$(hostname) - [$(date +%Y/%m/%d/%H:%M:%S)] \$ $2" >> "$proc_file_path"
        if [[ $1 == "1" ]]; then
            tr '\0' '\n' < $1 >> "$proc_file_path"
        elif [[ $1 == "2" ]]; then
            eval $2 2>&1 >> "$proc_file_path"
        fi
        echo -e "$split_line_symbol" >> "$proc_file_path"
    }

    redirect_output 1 "/proc/$pid/cmdline"
    redirect_output 1 "/proc/$pid/status"
    
    redirect_output 1 "/proc/$pid/environ"
    redirect_output 1 "/proc/$pid/maps"
    redirect_output 1 "/proc/$pid/stat"
    redirect_output 1 "/proc/$pid/io"

    redirect_output 1 "/proc/$pid/net/tcp"
    redirect_output 1 "/proc/$pid/net/udp"

    redirect_output 1 "/proc/$pid/sched"
    redirect_output 1 "/proc/$pid/schedstat"

    for tid in $(ls /proc/$pid/task); do
        redirect_output 1 "/proc/$pid/task/$tid/status"
    done

    redirect_output 2 "ls -l /proc/$pid/fd"
    redirect_output 2 "ls -l /proc/$pid/ns"
}

get_proc_lib_by_pid() {
    local pid=$1
    local maps_path="/proc/$pid/maps"

    grep -E ' r-xp ' $maps_path \
        | awk '{print $6}' \
        | while read -r file; do
            if [[ $file == *.so* ]]; then
                echo $file
            fi
        done
}

tar_file_by_pid() {
    local pid=$1
    local pid_file_path="$(readlink /proc/$pid/exe)"
    local pid_file_name="$(basename $pid_file_path)"
    local pid_tar_file_name="$pid_file_name.tar"

    echo [$pid]: $pid_file_path

    (cd $root_tar_dir_path && get_proc_lib_by_pid $pid | tar -cf $pid_tar_file_name -T -)
    (cd $root_tar_dir_path && get_runtime_info $pid && tar -rf $pid_tar_file_name -C $workdir $runtime_info_file_name)
    (cd $root_tar_dir_path && tar -rf $pid_tar_file_name -C "$(dirname $pid_file_path)" $pid_file_name)
}

tar_netstat_process() {
    netstat -antlup 2>/dev/null > "$root_tar_dir_path/netstat.log"
    for pid in $(netstat -antlup 2>/dev/null | awk '{print $7}' | grep -v '-' | grep -v 'Address' | awk -F/ '{print $1}' | sort | shuf) ; do
        (cd $root_tar_dir_path && tar_file_by_pid $pid)
    done
}

cd $workdir
(tar_netstat_process)
tar -cf $root_tar_file_name $root_tar_dir_path