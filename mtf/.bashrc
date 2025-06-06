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

# Configure git-aware prompt
configure_git_prompt() {
    git_prompt() {
        command -v git >/dev/null 2>&1 || return
        
        local git_status branch repo_name
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            branch=$(git symbolic-ref --short HEAD 2>/dev/null || git describe --tags --always 2>/dev/null)
            
            repo_name=$(basename -s .git $(git config --get remote.origin.url 2>/dev/null) 2>/dev/null || basename $(git rev-parse --show-toplevel 2>/dev/null))
            
            git_status=$(git status --porcelain 2>/dev/null)
            
            local status_color='\[\033[0;32m\]' 
            local status_text="clean"
            
            if [[ -n "$git_status" ]]; then
                local added_count=$(echo "$git_status" | grep -c "^A\|^??\|^ A")
                local modified_count=$(echo "$git_status" | grep -c "^M\|^ M")
                local deleted_count=$(echo "$git_status" | grep -c "^D\|^ D")
                
                status_color='\[\033[0;31m\]'
                status_text="commit"
                if [[ $added_count -gt 0 || $modified_count -gt 0 || $deleted_count -gt 0 ]]; then
                    local details=""
                    [[ $added_count -gt 0 ]] && details+="+$added_count"
                    [[ $modified_count -gt 0 ]] && details+="~$modified_count"
                    [[ $deleted_count -gt 0 ]] && details+="-$deleted_count"
                    status_text+="[$details]"
                fi
            elif git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null | grep -q -v "^0[[:space:]]0$"; then
                local ahead_behind=$(git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null)
                local behind=$(echo "$ahead_behind" | awk '{print $1}')
                local ahead=$(echo "$ahead_behind" | awk '{print $2}')
                
                status_color='\[\033[0;33m\]'
                status_text="sync"
                
                if [[ $ahead -gt 0 && $behind -gt 0 ]]; then
                    status_text+="[↓$behind↑$ahead]"
                elif [[ $ahead -gt 0 ]]; then
                    status_text+="[↑$ahead]"
                elif [[ $behind -gt 0 ]]; then
                    status_text+="[↓$behind]"
                fi
            fi
            
            printf -- "-(git/%s/%s)-%s(%s)\\[\\033[0m\\]" "$repo_name" "$branch" "$status_color" "$status_text"
        else
            echo ""
        fi
    }
    
    __update_ps1() {
        local git_info=$(git_prompt)
        
        case "$PROMPT_ALTERNATIVE" in
            twoline)
                PS1='\[\033[0;32m\]┌──${debian_chroot:+($debian_chroot)─}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))─}(\[\033[01;32m\]\u(.ᗜ ᴗ ᗜ.)\h\[\033[0;32m\])-[\[\033[0m\]\w\[\033[0;32m\]]'"$git_info"'\n\[\033[0;32m\]└─\[\033[01;34m\]\$\[\033[0m\] '
                ;;
            oneline)
                PS1='${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}\[\033[01;32m\]\u(.ᗜ ᴗ ᗜ.)\h\[\033[0m\]:\[\033[01;34m\]\w\[\033[0m\]'"$git_info"'\$ '
                ;;
            backtrack)
                PS1='${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}\[\033[01;31m\]\u(.ᗜ ᴗ ᗜ.)\h\[\033[0m\]:\[\033[01;34m\]\w\[\033[0m\]'"$git_info"'\$ '
                ;;
            *)
                PS1='\[\033[01;32m\]\u(.ᗜ ᴗ ᗜ.)\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]'"$git_info"'\$ '
                ;;
        esac
    }
    
    PROMPT_COMMAND="__update_ps1${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
}

# The following block is surrounded by two delimiters.
# These delimiters must not be modified. Thanks.
# START KALI CONFIG VARIABLES
PROMPT_ALTERNATIVE=twoline
NEWLINE_BEFORE_PROMPT=yes
# STOP KALI CONFIG VARIABLES

# Define prompt symbol globally
prompt_symbol="(.ᗜ ᴗ ᗜ.)"

if [ "$color_prompt" = yes ]; then
    # override default virtualenv indicator in prompt
    VIRTUAL_ENV_DISABLE_PROMPT=1

    configure_git_prompt
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

# Add a newline before prompt if configured
add_newline_before_prompt() {
    if [ "$NEWLINE_BEFORE_PROMPT" = yes ]; then
        if [ -z "$_NEW_LINE_BEFORE_PROMPT" ]; then
            _NEW_LINE_BEFORE_PROMPT=1
        else
            echo ""
        fi
    fi
}

PROMPT_COMMAND="add_newline_before_prompt${PROMPT_COMMAND:+; $PROMPT_COMMAND}"

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

# repo
github_url_base="https://raw.githubusercontent.com/shi9uma/genshin/main"
# local
leader_path_name="cargo"

# color, usage: ${RED}xxx${NC}
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
    DEFAULT_DIR='/tmp/tmp'
    while getopts "ch" opt; do
        case ${opt} in
            c )
                target_dir=$2
                target_dir_path="$DEFAULT_DIR/$target_dir"
                mkdir -p $target_dir_path
                echo -e "create dir: ${GREEN}$target_dir_path${NC}"
                return
                ;;
            h )
                echo -e "Usage: ${GREEN}tmp [-c] [dir]${NC}"
                echo -e "  ${GREEN}tmp [dir]${NC}: create dir and cd"
                echo -e "  ${GREEN}tmp -c [dir]${NC}: create dir but not cd"
                echo -e "  ${GREEN}tmp -h${NC}: help"
                return
                ;;
        esac
    done

    if [ $# -eq 0 ]; then
        mkdir -p $DEFAULT_DIR
        cd $DEFAULT_DIR
    elif [ $# -eq 1 ]; then
        mkdir -p $DEFAULT_DIR/$1
        cd $DEFAULT_DIR/$1
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
    curl --create-dirs -fLo $1 $2
}

w2u() {
    windows_path_like="$1"
    unix_path=$(echo "$windows_path_like" | sed 's|\\|/|g' | sed 's|^\([a-zA-Z]\):|/\L\1|')
    echo "$unix_path"
}

update_bashrc() {
    bashrc_path="$HOME/.bashrc"
    _curl $bashrc_path $github_url_base/mtf/.bashrc
}

find_path() {
    current_dir=$(pwd)
	if [ $# -eq 1 ]; then
		target_dir_name=$1
	else
		target_dir_name="$leader_path_name"
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

# Script-based functions
local_repo_path="$HOME/$leader_path_name/repo/04-flyMe2theStar/03-genshin"

call_bridge() {
    this_script_path="code/shellscript/07-call-bridge.sh"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        call_bridge_path="$local_repo_path/$this_script_path"
    else
        call_bridge_path="$HOME/.genshin/call-bridge.sh"
        if [[ ! -f $call_bridge_path ]]; then
            _curl $call_bridge_path $github_url_base/$this_script_path
            chmod +x $call_bridge_path
        fi
    fi
    eval "$call_bridge_path $@"
}

password() {
    this_script_path="code/python/08-password-generator.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        rename_path="$local_repo_path/$this_script_path"
    else
        rename_path="$HOME/.genshin/password-generator.py"
        if [[ ! -f $rename_path ]]; then
            _curl $rename_path $github_url_base/$this_script_path
        fi
    fi
    python3 $rename_path "$@"
}

cx() {
    this_script_path="code/python/09-ip-status.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        ip_status_path="$local_repo_path/$this_script_path"
    else
        ip_status_path="$HOME/.genshin/ip-status.py"
        if [[ ! -f $ip_status_path ]]; then
            _curl $ip_status_path $github_url_base/$this_script_path
        fi
    fi
    python3 $ip_status_path "$@"
}

lcd() {
    this_script_path="code/python/13-lcd.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        lcd_path="$local_repo_path/$this_script_path"
    else
        lcd_path="$HOME/.genshin/lcd.py"
        if [[ ! -f $lcd_path ]]; then
            _curl $lcd_path $github_url_base/$this_script_path
        fi
    fi
    if [[ "$1" == "cd" && ! -z "$2" ]]; then
        target_dir=$(python $lcd_path -g "$2")
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
    this_script_path="code/python/14-interact-rename.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        rename_path="$local_repo_path/$this_script_path"
    else
        rename_path="$HOME/.genshin/interact-rename.py"
        if [[ ! -f $rename_path ]]; then
            _curl $rename_path $github_url_base/$this_script_path
        fi
    fi
    python3 $rename_path "$@"
}

unblob() {
    this_script_path="code/shellscript/04-unblob.sh"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        unblob_path="$local_repo_path/$this_script_path"
    else
        unblob_path="$HOME/.genshin/unblob.sh"
        if [[ ! -f $unblob_path ]]; then
            _curl $unblob_path $github_url_base/$this_script_path
            chmod +x $unblob_path
        fi
    fi
    eval $unblob_path "$@"
}

ollama() {
    this_script_path="code/python/17-cli-ollama.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        ollama_path="$local_repo_path/$this_script_path"
    else
        ollama_path="$HOME/.ollama/cli-ollama.py"
        if [[ ! -f $ollama_path ]]; then
            mkdir -p "$HOME/.ollama"
            _curl $ollama_path $github_url_base/$this_script_path
        fi
    fi
    python3 $ollama_path "$@"
}

sd() {
    this_script_path="code/python/10-shodan.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        sd_path="$local_repo_path/$this_script_path"
    else
        sd_path="$HOME/.genshin/sd.py"
        if [[ ! -f $sd_path ]]; then
            _curl $sd_path $github_url_base/$this_script_path
        fi
    fi
    python3 $sd_path "$@"
}

fast_http_server() {
    this_script_path="code/python/16-fast-http-server.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        fast_http_server_path="$local_repo_path/$this_script_path"
    else
        fast_http_server_path="$HOME/.genshin/fast-http-server.py"
        if [[ ! -f $fast_http_server_path ]]; then
            _curl $fast_http_server_path $github_url_base/$this_script_path
        fi
    fi
    python3 $fast_http_server_path "$@"
}

encrypt() {
    this_script_path="code/python/02-ez-encrypt.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        encrypt_path="$local_repo_path/$this_script_path"
    else
        encrypt_path="$HOME/.genshin/ez-encrypt.py"
        if [[ ! -f $encrypt_path ]]; then
            _curl $encrypt_path $github_url_base/$this_script_path
        fi
    fi
    python3 $encrypt_path "$@"
}

# Conditional aliases
if [[ -f "$HOME/$leader_path_name/game/minecraft/tool/rcon.py" ]]; then
    alias mc="python $HOME/$leader_path_name/game/minecraft/tool/rcon.py"
fi

if [[ -d "$HOME/$leader_path_name" ]]; then
    alias home="cd $HOME/$leader_path_name"
fi

if [[ -d "$HOME/$leader_path_name/app" ]]; then
    alias app="cd $HOME/$leader_path_name/app"
fi

if [[ -d "$HOME/$leader_path_name/repo" ]]; then
    alias repo="cd $HOME/$leader_path_name/repo"
fi

# Export settings
## proxy
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

## vim
export FZF_DEFAULT_COMMAND="rg --files"
export FZF_DEFAULT_OPTS="-m --height 40% --reverse --border --ansi --preview '(highlight -O ansi {} || cat {}) 2> /dev/null | head -500'"

## app
os_type=$(uname -o)
export_path=$PATH
case $os_type in
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
        ;;
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
        
        alias typora="/Applications/Typora.app/Contents/MacOS/Typora"
        alias code="/Applications/VisualStudioCode.app/Contents/MacOS/Electron"
        alias bandizip="/Applications/Bandizip.app/Contents/MacOS/Bandizip"
        ;;
esac
export PATH=$export_path

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
