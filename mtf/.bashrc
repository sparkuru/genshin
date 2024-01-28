# Disable the default interactive shell warning
export BASH_SILENCE_DEPRECATION_WARNING=1

# ~/.bashrc file for bash interactive shells

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# History configurations
HISTFILE=~/.bash_history
HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and update LINES and COLUMNS if necessary
shopt -s checkwinsize

# enable autocd if bash version >= 4.0
if ((BASH_VERSINFO[0] >= 4)); then
    shopt -s autocd
fi

# configure `time` format
TIMEFORMAT=$'\nreal\t%3lR\nuser\t%3lU\nsys\t%3lS\ncpu\t%P'

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
    else
        color_prompt=
    fi
fi

# Configure prompt
if [ "$color_prompt" = yes ]; then
    # Use a more advanced prompt similar to zsh
    PS1='\[\033[01;32m\]\u\[\033[00m\]@\[\033[01;32m\]\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title
case "$TERM" in
xterm*|rxvt*|Eterm|aterm|kterm|gnome*|alacritty)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    export LS_COLORS="$LS_COLORS:ow=30;44:" # fix ls color for folders with 777 permissions
    
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
    alias diff='diff --color=auto'
    alias ip='ip --color=auto'
    
    # LESS colors for man pages
    export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
    export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
    export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
    export LESS_TERMCAP_so=$'\E[01;33m'    # begin reverse video
    export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
    export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
    export LESS_TERMCAP_ue=$'\E[0m'        # reset underline
fi

# ==============================================================
# |                       custom script                         |
# ==============================================================

github_url_base="https://raw.githubusercontent.com/shi9uma/genshin/main"

# color
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions
cmd() {
    sed -n '/^# anchor$/,/^# end alias$/p' ~/.bashrc | awk '
    BEGIN { 
        color_alias="\033[0;36m";
        color_alias_name="\033[0;32m";
        color_alias_cmd="\033[0;33m";
        reset="\033[0m";
    }
    /^alias/ {
        cmd = $0;
        sub(/^alias[ \t]+/, "", cmd);
        split(cmd, parts, "=");
        alias_name = parts[1];
        alias_cmd = substr(parts[2], 2, length(parts[2]) - 2);
        printf("%salias %s%-10s%s = %s\"%s\"%s\n", color_alias, color_alias_name, alias_name, reset, color_alias_cmd, alias_cmd, reset);
        next;
    }
    {
        print $0;
    }'
}

tmp() {
    if [ $# -eq 0 ]; then
        mkdir -p '/tmp/tmp'
        cd /tmp/tmp
    elif [ $# -eq 1 ]; then
        mkdir -p /tmp/tmp/$1
        cd /tmp/tmp/$1
    else
        echo "usage: tmp [dir]"
    fi
}

tsh() {
    new_shell_script=$1
    if [[ "$new_shell_script" != /* ]]; then
        new_shell_script="$PWD/$new_shell_script"
    fi
    if [[ ! -f "$new_shell_script" ]]; then
        touch $new_shell_script
        chmod +x $new_shell_script
        echo $new_shell_script
    fi
}

clean_history() {
    history -c -w
    echo "" > ~/.bash_history
    kill -9 $$
}

clean_docker() {
    docker rm $(docker ps -a | grep Exited | awk '{ print $1 }') > /dev/null 2>&1
    docker rmi $(docker images | grep -i \<none\> | awk '{ print $3 }') > /dev/null 2>&1

    docker images; echo ""
    docker ps -a
}

_curl() {
    curl -fLo $1 --create-dirs $2
}

password() {
    rename_path="$HOME/.genshin/password-generator.py"
    if [[ ! -f $rename_path ]]; then
        _curl $rename_path $github_url_base/code/python/08-password-generator.py
    fi
    python3 $rename_path "$@"
}

cx() {
    ip_status_path="$HOME/.genshin/ip-status.py"
    if [[ ! -f $ip_status_path ]]; then
        _curl $ip_status_path $github_url_base/code/python/09-ip-status.py
    fi
    python3 $ip_status_path "$@"
}

lcd() {
    lcd_path="$HOME/.genshin/lcd.py"
    if [[ ! -f $lcd_path ]]; then
        _curl $lcd_path $github_url_base/code/python/13-lcd.py
    fi
    if [[ "$1" == "cd" && ! -z "$2" ]]; then
        target_dir=$(python $lcd_path -pn "$2")
        cd "$target_dir"
    elif [[ "$1" == "l" ]]; then
        python3 $lcd_path -l
    elif [[ "$1" == "d" && ! -z "$2" ]]; then
        python3 $lcd_path -d -n "$2"
    elif [[ "$1" == "a" && ! -z "$2" ]]; then
        python3 $lcd_path -a "$2"
    else
        python3 $lcd_path "$@"
    fi
}

rename() {
    rename_path="$HOME/.genshin/interact-rename.py"
    if [[ ! -f $rename_path ]]; then
        _curl $rename_path $github_url_base/code/python/14-interact-rename.py
    fi
    python3 $rename_path "$@"
}

w2u() {
    windows_path_like="$1"
    unix_path=$(echo "$windows_path_like" | sed 's|\\|/|g' | sed 's|^\([a-zA-Z]\):|/\L\1|')
    echo "$unix_path"
}

sd() {
    sd_path="$HOME/.genshin/sd.py"
    if [[ ! -f $sd_path ]]; then
        _curl $sd_path $github_url_base/code/python/10-shodan.py
    fi
    python3 $sd_path "$@"
}

unblob() {
    unblob_path="$HOME/.genshin/unblob.sh"
    if [[ ! -f $unblob_path ]]; then
        _curl $unblob_path $github_url_base/code/shellscript/04-unblob.sh
        chmod +x $unblob_path
    fi
    cp $unblob_path .
    eval $PWD/unblob.sh $1
}

call_bridge() {
    call_bridge_path="$HOME/.genshin/call-bridge.sh"
    if [[ ! -f $call_bridge_path ]]; then
        _curl $call_bridge_path $github_url_base/code/shellscript/07-call-bridge.sh
        chmod +x $call_bridge_path
    fi
    eval "$call_bridge_path $@"
}

update_bashrc() {
    bashrc_path="$HOME/.bashrc"
    _curl $bashrc_path $github_url_base/mtf/.bashrc
}

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
            echo "$current_dir"
            return 0
        fi
        current_dir=$(dirname "$current_dir")
    done

    echo -e "${RED}Error: $target_dir_name directory not found${NC}"
    return 1
}

# 从zshrc添加的新函数
ollama() {
    ollama_dir_path="$HOME/.ollama"
    if [[ ! -d $ollama_dir_path ]]; then
        mkdir -p $ollama_dir_path
    fi
    ollama_path="$ollama_dir_path/cli-ollama.py"
    if [[ ! -f $ollama_path ]]; then
        _curl $ollama_path $github_url_base/code/python/17-cli-ollama.py
    fi
    python3 $ollama_path "$@"
}

exp() {
    if [[ ! -f "/usr/bin/dolphin" ]]; then
        echo -e "${RED}dolphin not found, try ${GREEN}sudo apt install dolphin-emu${NC}"
        return 1
    fi
    if [[ $# -eq 0 ]]; then
        dolphin . &>/dev/null &
    else
        dolphin "$@" &>/dev/null &
    fi
    return 0
}

## file, dir
if [[ -f "/home/game/minecraft/tool/rcon.py" ]]; then
    alias mc="python /home/game/minecraft/tool/rcon.py"
fi

# 从zshrc添加的目录别名
leader_path_name="cargo"
if [[ -d "$HOME/$leader_path_name" ]]; then
    alias home="cd $HOME/$leader_path_name"
fi
if [[ -d "$HOME/$leader_path_name/app" ]]; then
    alias app="cd $HOME/$leader_path_name/app"
fi
if [[ -d "$HOME/$leader_path_name/repo" ]]; then
    alias repo="cd $HOME/$leader_path_name/repo"
fi
# 保留原有的repo别名
if [[ ! -d "$HOME/$leader_path_name/repo" && -d "$HOME/repo" ]]; then
    alias repo="cd $HOME/repo"
fi

## export
proxy_ip_file="$HOME/.proxy-ip"
if [[ -f $proxy_ip_file ]]; then
    if [[ $(cat $proxy_ip_file) == "no proxy" ]]; then
        :
    elif [[ $( stat -c %s $proxy_ip_file) -eq 0 ]]; then
        echo -e "${RED}proxy ip file: $proxy_ip_file is empty, delete it or ${GREEN}echo 'ip port' > \$proxy_ip_file${NC} ${NC}"
    else
        proxy_ip=$(cat $proxy_ip_file | awk '{print $1}')
        proxy_port=$(cat $proxy_ip_file | awk '{print $2}')

        if [[ -z "$proxy_port" ]]; then
            proxy_port=1080
        fi
        export all_proxy="http://$proxy_ip:$proxy_port"
    fi
else
    if [[ -d "/home/$USER" ]]; then
        echo -e "${RED}proxy ip file: $proxy_ip_file not found, try ${NC}${GREEN}echo 'ip port' > \$proxy_ip_file${NC}"
        echo -e "${RED}or ${GREEN}echo 'no proxy' > \$proxy_ip_file ${NC}${RED}for no proxy needed${NC}"
    fi
fi

### vim
export FZF_DEFAULT_COMMAND="rg --files"
export FZF_DEFAULT_OPTS="-m --height 40% --reverse --border --ansi --preview '(highlight -O ansi {} || cat {}) 2> /dev/null | head -500'"

### binary
os_type=$(uname -o)
export_path=$PATH
case $os_type in
    "Darwin")
        export CLICOLOR=1
        export LSCOLORS=ExGxBxDxCxEgEdxbxgxcxd

        darwin_paths=(
            "$HOME/.bin"
            "$HOME/.local/bin"
            "$HOME/.cargo/bin"
            "/usr/lib/nodejs/bin"
            "/opt/homebrew/bin"
            "/opt/homebrew/opt/make/libexec/gnubin"
            "/opt/metasploit-framework/bin"
        )

        export_path=$PATH
        for path in "${darwin_paths[@]}"; do
            if [[ -d "$path" ]]; then
                export_path="$path:$export_path"
            fi
        done
        
        # alias python="/opt/homebrew/bin/python3"
        # alias pip="/opt/homebrew/bin/pip3"

        alias typora="/Applications/Typora.app/Contents/MacOS/Typora"
        alias code="/Applications/VisualStudioCode.app/Contents/MacOS/Electron"
        alias bandizip="/Applications/Bandizip.app/Contents/MacOS/Bandizip"
        ;;
    "GNU/Linux")
        linux_paths=(
            "$HOME/.bin"
            "$HOME/.local/bin"
            "$HOME/.cargo/bin"
            "/usr/lib/nodejs/bin"
        )

        export_path=$PATH
        for path in "${linux_paths[@]}"; do
            if [[ -d "$path" ]]; then
                export_path="$path:$export_path"
            fi
        done
        
        alias python="env -u PYTHONHOME -u PYTHONPATH python"
        alias pip="env -u PYTHONHOME -u PYTHONPATH pip"
        ;;
esac
export PATH=$export_path

if [[ -z "$DONT_FASTFETCH" || $DONT_FASTFETCH -ne 1 ]]; then
    if [ -f /usr/bin/fastfetch ]; then
        fastfetch
    fi
fi

# anchor
# ==============================================================
# |                       custom alias                         |
# ==============================================================

# alias
alias l="ls -ah"
alias ll="ls -alh"
alias lt="ls -alht"
alias lss="ls -alhS"
alias cls="clear"
alias c="clear"
alias size="du -abh --time -d 1"
    # exclude file size under 1G: `size -t 1G`;
    # exclude reg files: `size --exclude=*backups*`;
    # sort by size: `size | sort -h`

alias rcp="rsync -avtz --progress"
    # use ssh option: `rcp -e "ssh -p 22000 -i ~/.ssh/id_rsa" src user@host:/path/to/dst`

alias x="curl"
alias xi="curl -I"
alias reg="grep -ir"
alias bashrc="source ~/.bashrc"
alias f="fastfetch"
alias transfer="sd search http.favicon.hash:-620522584"
alias random="cat /dev/urandom|head|base64|md5sum|cut -d \" \" -f 1"
# end alias
