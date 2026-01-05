# ~/.zshrc file for zsh interactive shells.
# see /usr/share/doc/zsh/examples/zshrc for examples

setopt autocd              # change directory just by typing its name
#setopt correct            # auto correct mistakes
setopt interactivecomments # allow comments in interactive mode
setopt magicequalsubst     # enable filename expansion for arguments of the form 'anything=expression'
setopt nonomatch           # hide error message if there is no match for the pattern
setopt notify              # report the status of background jobs immediately
setopt numericglobsort     # sort filenames numerically when it makes sense
setopt promptsubst         # enable command substitution in prompt

WORDCHARS=${WORDCHARS//\/} # Don't consider certain characters part of the word

# hide EOL sign ('%')
PROMPT_EOL_MARK=""

# configure key keybindings
bindkey -e                                        # emacs key bindings
bindkey ' ' magic-space                           # do history expansion on space
bindkey '^U' backward-kill-line                   # ctrl + U
bindkey '^[[3;5~' kill-word                       # ctrl + Supr
bindkey '^[[3~' delete-char                       # delete
bindkey '^[[1;5C' forward-word                    # ctrl + ->
bindkey '^[[1;5D' backward-word                   # ctrl + <-
bindkey '^[[5~' beginning-of-buffer-or-history    # page up
bindkey '^[[6~' end-of-buffer-or-history          # page down
bindkey '^[[H' beginning-of-line                  # home
bindkey '^[[F' end-of-line                        # end
bindkey '^[[Z' undo                               # shift + tab undo last action

# enable completion features
autoload -Uz compinit
compinit -d ~/.cache/zcompdump
zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' rehash true
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'

# History configurations
HISTFILE=~/.zsh_history
HISTSIZE=1000
SAVEHIST=2000
setopt hist_expire_dups_first # delete duplicates first when HISTFILE size exceeds HISTSIZE
setopt hist_ignore_dups       # ignore duplicated commands history list
setopt hist_ignore_space      # ignore commands that start with space
setopt hist_verify            # show command with history expansion to user before running it
#setopt share_history         # share command history data

# force zsh to show the complete history
alias history="history 0"

# configure `time` format
TIMEFMT=$'\nreal\t%E\nuser\t%U\nsys\t%S\ncpu\t%P'

# make less more friendly for non-text input files, see lesspipe(1)
#[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # We have color support; assume it's compliant with Ecma-48
        # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
        # a case would tend to support setf rather than setaf.)
        color_prompt=yes
    else
        color_prompt=
    fi
fi

configure_prompt() {    

    # prompt_symbol="(.ᗜ ᴗ ᗜ.)"
    prompt_symbol="(🌸.ᗜ ᴗ ᗜ.)"

    if [ "$is_incognito" ]; then
        prompt_symbol="%F{red}$prompt_symbol！%F{%(#.red.blue)}"
    fi

    git_prompt() {
        command -v git >/dev/null 2>&1 || return
        
        local git_status branch repo_name
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            branch=$(git symbolic-ref --short HEAD 2>/dev/null || git describe --tags --always 2>/dev/null)
            
            repo_name=$(basename -s .git $(git config --get remote.origin.url 2>/dev/null) 2>/dev/null || basename $(git rev-parse --show-toplevel 2>/dev/null))
            
            git_status=$(git status --porcelain 2>/dev/null)
            
            local status_color="%F{green}" 
            local status_text="clean"
            
            if [[ -n "$git_status" ]]; then
                local added_count=$(echo "$git_status" | grep -c "^A\|^??\|^ A")
                local modified_count=$(echo "$git_status" | grep -c "^M\|^ M")
                local deleted_count=$(echo "$git_status" | grep -c "^D\|^ D")
                
                status_color="%F{red}"
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
                
                status_color="%F{yellow}"
                status_text="sync"
                
                if [[ $ahead -gt 0 && $behind -gt 0 ]]; then
                    status_text+="[↓$behind↑$ahead]"
                elif [[ $ahead -gt 0 ]]; then
                    status_text+="[↑$ahead]"
                elif [[ $behind -gt 0 ]]; then
                    status_text+="[↓$behind]"
                fi
            fi
            
            echo "-(git/$repo_name/$branch)-${status_color}($status_text)%f"
        else
            echo ""
        fi
    }
    
    case "$PROMPT_ALTERNATIVE" in
        twoline)
            PROMPT=$'%F{%(#.blue.green)}┌──${debian_chroot:+($debian_chroot)─}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))─}(%B%F{%(#.red.blue)}%n'$prompt_symbol$'%m%b%F{%(#.blue.green)})-[%B%F{reset}%(6~.%-1~/…/%4~.%5~)%b%F{%(#.blue.green)}]$(git_prompt)\n%F{%(#.blue.green)}└─%B%(#.%F{red}#.%F{blue}$)%b%F{reset} '
            # Right-side prompt with exit codes and background processes
            #RPROMPT=$'%(?.. %? %F{red}%B⨯%b%F{reset})%(1j. %j %F{yellow}%B⚙%b%F{reset}.)'
            ;;
        oneline)
            PROMPT=$'${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%B%F{%(#.red.blue)}%n@%m%b%F{reset}:%B%F{%(#.blue.green)}%~%b%F{reset}$(git_prompt)%(#.#.$) '
            RPROMPT=
            ;;
        backtrack)
            PROMPT=$'${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%B%F{red}%n@%m%b%F{reset}:%B%F{blue}%~%b%F{reset}$(git_prompt)%(#.#.$) '
            RPROMPT=
            ;;
    esac
    unset prompt_symbol
}

function precmd_update_git_vars() {
    if [ -n "$__EXECUTED_GIT_COMMAND" ]; then
        update_current_git_vars
        unset __EXECUTED_GIT_COMMAND
    fi
}

function preexec_update_git_vars() {
    case "$1" in
        git*|hub*|gh*|stg*)
            __EXECUTED_GIT_COMMAND=1
            ;;
    esac
}

precmd_functions+=(precmd_update_git_vars)
preexec_functions+=(preexec_update_git_vars)

function update_current_git_vars() {
    unset __CURRENT_GIT_STATUS
    
    command -v git >/dev/null 2>&1 || return
    
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        __CURRENT_GIT_STATUS=1
    else
        unset __CURRENT_GIT_STATUS
    fi
}

# The following block is surrounded by two delimiters.
# These delimiters must not be modified. Thanks.
# START KALI CONFIG VARIABLES
PROMPT_ALTERNATIVE=twoline
NEWLINE_BEFORE_PROMPT=yes
# STOP KALI CONFIG VARIABLES

if [ "$color_prompt" = yes ]; then
    # override default virtualenv indicator in prompt
    VIRTUAL_ENV_DISABLE_PROMPT=1

    configure_prompt

    # enable syntax-highlighting
    if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
        . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
        ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern)
        ZSH_HIGHLIGHT_STYLES[default]=none
        ZSH_HIGHLIGHT_STYLES[unknown-token]=underline
        ZSH_HIGHLIGHT_STYLES[reserved-word]=fg=cyan,bold
        ZSH_HIGHLIGHT_STYLES[suffix-alias]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[global-alias]=fg=green,bold
        ZSH_HIGHLIGHT_STYLES[precommand]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[commandseparator]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[autodirectory]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[path]=bold
        ZSH_HIGHLIGHT_STYLES[path_pathseparator]=
        ZSH_HIGHLIGHT_STYLES[path_prefix_pathseparator]=
        ZSH_HIGHLIGHT_STYLES[globbing]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[history-expansion]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[command-substitution]=none
        ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[process-substitution]=none
        ZSH_HIGHLIGHT_STYLES[process-substitution-delimiter]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[single-hyphen-option]=fg=green
        ZSH_HIGHLIGHT_STYLES[double-hyphen-option]=fg=green
        ZSH_HIGHLIGHT_STYLES[back-quoted-argument]=none
        ZSH_HIGHLIGHT_STYLES[back-quoted-argument-delimiter]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[single-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[double-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[rc-quote]=fg=magenta
        ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[back-double-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[back-dollar-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[assign]=none
        ZSH_HIGHLIGHT_STYLES[redirection]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[comment]=fg=black,bold
        ZSH_HIGHLIGHT_STYLES[named-fd]=none
        ZSH_HIGHLIGHT_STYLES[numeric-fd]=none
        ZSH_HIGHLIGHT_STYLES[arg0]=fg=cyan
        ZSH_HIGHLIGHT_STYLES[bracket-error]=fg=red,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-1]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-2]=fg=green,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-3]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-4]=fg=yellow,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-5]=fg=cyan,bold
        ZSH_HIGHLIGHT_STYLES[cursor-matchingbracket]=standout
    fi
else
    PROMPT='${debian_chroot:+($debian_chroot)}%n@%m:%~%(#.#.$) '
fi
unset color_prompt force_color_prompt

toggle_oneline_prompt(){
    if [ "$PROMPT_ALTERNATIVE" = oneline ]; then
        PROMPT_ALTERNATIVE=twoline
    else
        PROMPT_ALTERNATIVE=oneline
    fi
    configure_prompt
    zle reset-prompt
}
zle -N toggle_oneline_prompt
bindkey ^P toggle_oneline_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*|Eterm|aterm|kterm|gnome*|alacritty)
    TERM_TITLE=$'\e]0;${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%n@%m: %~\a'
    ;;
*)
    ;;
esac

precmd() {
    # Print the previously configured title
    print -Pnr -- "$TERM_TITLE"

    # Print a new line before the prompt, but only if it is not the first line
    if [ "$NEWLINE_BEFORE_PROMPT" = yes ]; then
        if [ -z "$_NEW_LINE_BEFORE_PROMPT" ]; then
            _NEW_LINE_BEFORE_PROMPT=1
        else
            print ""
        fi
    fi
}

# enable color support of ls, less and man, and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    export LS_COLORS="$LS_COLORS:ow=30;44:" # fix ls color for folders with 777 permissions

    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
    alias diff='diff --color=auto'
    alias ip='ip --color=auto'

    export LESS_TERMCAP_mb=$'\e[1;32m'     # begin blink
    export LESS_TERMCAP_md=$'\e[1;32m'     # begin bold
    export LESS_TERMCAP_me=$'\e[0m'        # reset bold/blink
    export LESS_TERMCAP_so=$'\e[01;33m'    # begin reverse video
    export LESS_TERMCAP_se=$'\e[0m'        # reset reverse video
    export LESS_TERMCAP_us=$'\e[1;4;31m'     # begin underline
    export LESS_TERMCAP_ue=$'\e[0m'        # reset underline

    # Take advantage of $LS_COLORS for completion as well
    zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
    zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
fi

if [ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
    # change suggestion color
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#999'
fi

# enable command-not-found if installed
if [ -f /etc/zsh_command_not_found ]; then
    . /etc/zsh_command_not_found
fi

# ----------------------------------------- custom script ----------------------------------------- #

# repo
github_url_base="https://raw.githubusercontent.com/sparkuru/genshin/main"
# local
leader_path_name="cargo"

# color, usage: ${RED}xxx${NC}
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# custom function
## base on default cmd
cmd() {
    sed -n '/^## alias_anchor$/,/^## end_alias_anchor$/p' ~/.zshrc | awk '
    BEGIN { 
        color_alias="\033[0;36m";
        color_alias_name="\033[0;32m";
        color_alias_cmd="\033[0;33m";
        reset="\033[0m";
    }
    /^alias/ {
        cmd = $0;
        sub(/^alias[ \t]+/, "", cmd);
        eq_pos = index(cmd, "=");
        if (eq_pos > 0) {
            alias_name = substr(cmd, 1, eq_pos - 1);
            alias_cmd = substr(cmd, eq_pos + 1);
            gsub(/^["'\'']|["'\'']$/, "", alias_cmd);
            printf("%salias %s%-10s%s = %s\"%s\"%s\n", color_alias, color_alias_name, alias_name, reset, color_alias_cmd, alias_cmd, reset);
        }
        next;
    }
    {
        print $0;
    }'
}

tmp() {
    DEFAULT_DIR='/tmp/tmp'
    while getopts "cmh" opt; do
        case ${opt} in
            c )
                target_dir=$2
                target_dir_path="$DEFAULT_DIR/$target_dir"
                mkdir -p $target_dir_path
                echo "create dir: ${GREEN}$target_dir_path${NC}"
                return
                ;;
            m )
                target_name=$2
                target_path="$DEFAULT_DIR/$(basename $target_name)"
                if [[ -f "$target_path" ]]; then
                    echo "${RED}Error: ${GREEN}$target_path${RED} already exists${NC}"
                    return 1
                fi
                mv $2 $target_path
                if [[ $? -eq 0 ]]; then
                    echo "move file: ${GREEN}$2${NC} to ${GREEN}$target_path${NC}"
                else
                    echo "${RED}Error: ${GREEN}$2${RED} move failed${NC}"
                fi
                return
                ;;
            h )
                echo "Usage: ${GREEN}tmp [-c] [dir]${NC}"
                echo "  ${GREEN}tmp [dir]${NC}: create dir and cd"
                echo "  ${GREEN}tmp -c [dir]${NC}: create dir but not cd"
                echo "  ${GREEN}tmp -m [file path]${NC}: move file"
                echo "  ${GREEN}tmp -h${NC}: help"
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
    echo "" > ~/.zsh_history
    kill -9 $$
}

clean_docker() {
    docker rm `docker ps -a | grep Exited | awk '{ print $1 }'` > /dev/null 2>&1
    docker rmi `docker images | grep -i \<none\> | awk '{ print $3 }'` > /dev/null 2>&1
    docker volume prune > /dev/null 2>&1
    docker network prune > /dev/null 2>&1

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

update_zshrc() {
    zshrc_path="$HOME/.zshrc"
    if [[ ! -f $zshrc_path ]]; then
        _curl $zshrc_path $github_url_base/mtf/.zshrc
    fi
}

find_path() {
    current_dir=$(pwd)

    while getopts "fh" opt; do
        case ${opt} in
            f )
                fuzzy_match=true
                ;;
            h )
                echo "Usage: ${GREEN}find_path [-f for fuzzy match] [target_path_name]${NC}"
                return 0
                ;;
        esac
    done

    shift $((OPTIND-1))
    
	if [ $# -eq 1 ]; then
		target_dir_name=$1
	fi

    while [[ "$current_dir" != "/" ]]; do
        base_name=$(basename "$current_dir")

        if [[ "$fuzzy_match" == true ]]; then
            if [[ "$base_name" == *"$target_dir_name"* ]]; then
                echo "$current_dir"
                OPTIND=1
                return 0
            fi
        else
            if [[ "$base_name" == "$target_dir_name" ]]; then
                echo "$current_dir"
                return 0
            fi
        fi
        current_dir=$(dirname "$current_dir")
    done

    echo -e "${RED}Error: ${GREEN}$target_dir_name${RED} directory not found${NC}"
    return 1
}

exp() {
    if [[ ! -f "/usr/bin/dolphin" ]]; then
        echo "${RED}dolphin not found, try ${GREEN}sudo apt install dolphin-emu${NC}"
        return 1
    fi
    if [[ $# -eq 0 ]]; then
        dolphin . &>/dev/null &
    else
        dolphin "$@" &>/dev/null &
    fi
    return 0
}

sm() {
    export is_incognito=1
    source ~/.zshrc
    fc -p /dev/null 0 0

    incognito_precmd() {
        echo "${RED}incognito mode, type ${GREEN}xsm${RED} to exit.${NC}"
    }

    precmd_functions+=(incognito_precmd)

    xsm() {

        echo "${RED}exit incognito mode.${NC}"

        precmd_functions=(${precmd_functions[@]/incognito_precmd})

        unset is_incognito
        source ~/.zshrc

        fc -P
    }
}

md5() {
    if [[ $# -eq 0 ]]; then
        echo "fast md5sum hash generator, usage: ${GREEN}md5 [string | file] [string | file] ...${NC}"
        return 1
    fi

    _echo() {
        echo "${RED}$1${NC}: ${GREEN}$2${NC}"
    }
    hash_file() {
        _echo "$1" "$(md5sum "$1" | awk '{print $1}')"
    }
    hash_string() {
        _echo "$1" "$(echo -n "$1" | md5sum | awk '{print $1}')"
    }

    if [[ $# -eq 1 ]]; then
        if [[ -f "$1" ]]; then
            hash_file "$1"
        else
            hash_string "$1"
        fi
    else
        for arg in "$@"; do
            if [[ -f "$arg" ]]; then
                hash_file "$arg"
            else
                hash_string "$arg"
            fi
        done
    fi
}

ggit() {
    commit_comment="u1x:wq"
    case "$1" in
        push)
            if [ $(git pull -q; echo $?) -eq 0 ]; then
                git push
            else
                echo "pulled, but conflict or sth, manual resolve first."
                return 1
            fi
            ;;
		status)
			git status
			;;
        commit)
            local msg="${2:-$commit_comment}"
            git_root_dir=$(git rev-parse --show-toplevel)
            git add $git_root_dir && git commit -m "$msg"
            ;;
        auto)
            ggit commit "$2" && ggit push
            ;;
        root)
            current_dir=$(pwd)
            git_root_dir=$(git rev-parse --show-toplevel)
            echo -n "current path: ${RED}$current_dir${NC}\nchange to: ${GREEN}$git_root_dir${NC}"
            cd $git_root_dir
            ;;
        path)
            if [[ -z "$2" ]]; then
                echo "usage: ggit path <file_path>"
                return 1
            fi

            local target_path="$2"
            if [[ ! "$target_path" = /* ]]; then
                target_path="$(pwd)/$target_path"
            fi
            target_path=$(realpath "$target_path" 2>/dev/null)

            if [[ ! -e "$target_path" ]]; then
                echo "file not found: $target_path"
                return 1
            fi

            local target_dir
            if [[ -d "$target_path" ]]; then
                target_dir="$target_path"
            else
                target_dir=$(dirname "$target_path")
            fi

            local git_root=$(cd "$target_dir" && git rev-parse --show-toplevel 2>/dev/null)
            if [[ -z "$git_root" ]]; then
                echo "not a git repository: $target_dir"
                return 1
            fi

            local remote_url=$(cd "$git_root" && git remote get-url origin 2>/dev/null)
            if [[ -z "$remote_url" ]]; then
                echo "no remote origin found"
                return 1
            fi

            local user repo
            if [[ "$remote_url" =~ ^git@github\.com:(.+)/(.+)\.git$ ]]; then
                user="${match[1]}"
                repo="${match[2]}"
            elif [[ "$remote_url" =~ ^https://github\.com/(.+)/(.+)(\.git)?$ ]]; then
                user="${match[1]}"
                repo="${match[2]%.git}"
            else
                echo "unsupported remote url format: $remote_url"
                return 1
            fi

            local branch=$(cd "$git_root" && git branch --show-current)
            local rel_path="${target_path#$git_root/}"
            local raw_url="https://raw.githubusercontent.com/$user/$repo/refs/heads/$branch/$rel_path"
            echo "$raw_url"
            ;;
        *)
            echo "usage: ggit {push | commit [commit_msg] | auto [commit_msg] | root | path <file_path>}"
            return 1
            ;;
    esac
}

activate() {
    default_max_depth=3
    current_path=$(pwd)
    pyvenv_cfg_path=$(find $current_path -maxdepth $default_max_depth -type f -path "*/.pyvenv.cfg")
    if [[ -z "$pyvenv_cfg_path" ]]; then
        echo "${RED}no venv found${NC}"
        return 1
    fi
    python_venv_root_path=$(dirname "$pyvenv_cfg_path")
    source "$python_venv_root_path/bin/activate"
    echo "${GREEN}activated venv: $python_venv_root_path${NC}"
}


## base on custom script, python, shellscript, etc.
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

hftp() {
    this_script_path="code/python/16-hftp.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        hftp_path="$local_repo_path/$this_script_path"
    else
        hftp_path="$HOME/.genshin/hftp.py"
        if [[ ! -f $hftp_path ]]; then
            _curl $hftp_path $github_url_base/$this_script_path
        fi
    fi
    python3 $hftp_path "$@"
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

treec() {
    this_script_path="code/python/15-tree-creator.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        tree_creator_path="$local_repo_path/$this_script_path"
    else
        tree_creator_path="$HOME/.genshin/tree-creator.py"
        if [[ ! -f $tree_creator_path ]]; then
            _curl $tree_creator_path $github_url_base/$this_script_path
        fi
    fi
    python3 $tree_creator_path "$@"
}

tldr() {
    this_script_path="code/python/19-tldr.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        tldr_path="$local_repo_path/$this_script_path"

        tldr_config_dir_path="$HOME/cargo/repo/25-tldr"
        if [[ ! -d $tldr_config_dir_path ]]; then
            tldr_config_dir_path="$HOME/.genshin/tldr"
        fi
    else
        tldr_path="$HOME/.genshin/tldr.py"
        if [[ ! -f $tldr_path ]]; then
            _curl $tldr_path $github_url_base/$this_script_path
        fi

        tldr_config_dir_path="$HOME/.genshin/tldr"
        if [[ ! -d $tldr_config_dir_path ]]; then
            mkdir -p $tldr_config_dir_path
            git clone https://github.com/sparkuru/tldr.git $tldr_config_dir_path
        fi
    fi
    python3 $tldr_path --config-dir $tldr_config_dir_path "$@"
}

request2curl() {
    this_script_path="code/python/23-http-request-to-curl.py"
    if [[ -f "$local_repo_path/$this_script_path" ]]; then
        request2curl_path="$local_repo_path/$this_script_path"
    else
        request2curl_path="$HOME/.genshin/http-request-to-curl.py"
    fi
    python3 $request2curl_path "$@"
}

# export
## proxy
proxy_ip_file="$HOME/.proxy-ip"
if [[ -f $proxy_ip_file ]]; then

    if [[ $(cat $proxy_ip_file) == "no proxy" ]]; then
        :
    elif [[ $( stat -c %s $proxy_ip_file) -eq 0 ]]; then
        echo "${RED}proxy ip file: $proxy_ip_file is empty, delete it or ${GREEN}echo 'ip port' > \$proxy_ip_file${NC} ${NC}"
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
        echo "${RED}proxy ip file: $proxy_ip_file not found, try ${NC}${GREEN}echo 'ip port' > \$proxy_ip_file${NC}"
        echo "${RED}or ${GREEN}echo 'no proxy' > \$proxy_ip_file ${NC}${RED}for no proxy needed${NC}"
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
        linux_path=(
            "$HOME/.bin"
            "$HOME/.local/bin"
            "$HOME/.cargo/bin"
            "/usr/lib/nodejs/bin"
            "$export_path"
        )

        for path in "${linux_path[@]}"; do
            if [[ -d "$path" ]]; then
                export_path="$path:$export_path"
            fi
        done
        ;;
    "Darwin")
        export CLICOLOR=1
        export LSCOLORS=ExGxBxDxCxEgEdxbxgxcxd

        python_version=$(python3 --version 2>/dev/null | awk '{print $2}' | cut -d. -f1)
        python_base_version=$(echo $python_version | cut -d. -f1,2)
        
        darwin_path=(
            "$HOME/.bin"
            "$HOME/.local/bin"
            "$HOME/.cargo/bin"
            "$HOME/Library/Python/$python_base_version/bin"
            "/usr/lib/nodejs/bin"

            "/opt/homebrew/bin"
            "/opt/homebrew/opt/make/libexec/gnubin"
            "/opt/metasploit-framework/bin"

            "$export_path"
        )

        for path in "${darwin_path[@]}"; do
            if [[ -d "$path" ]]; then
                export_path="$path:$export_path"
            fi
        done
        ;;
esac
export PATH=$export_path

# alias
## condition alias
if [[ -f "$HOME/$leader_path_name/game/minecraft/tool/rcon.py" ]]; then
    alias mc="python $HOME/$leader_path_name/game/minecraft/tool/rcon.py"
fi

if [[ -d "$HOME/$leader_path_name/repo" ]]; then
    alias repo="cd $HOME/$leader_path_name/repo"
fi

if [[ -d "$HOME/$leader_path_name/repo/04-flyMe2theStar/03-genshin" ]]; then
    export genshin="$HOME/$leader_path_name/repo/04-flyMe2theStar/03-genshin"
    alias genshin="cd $genshin"
fi

## alias_anchor

alias l="ls -ah"
alias ll="ls -alh"
alias lt="ls -alht"
alias lss="ls -alhS"
alias c="clear"
alias cls="clear"
alias x="curl -f"
alias xi="curl -I -sfL"
alias xl="curl -sfL"
alias less="less -N"
alias zshrc="source ~/.zshrc"
alias random="cat /dev/urandom|head|base64|md5sum|cut -d \" \" -f 1"
alias p="ipython3"
alias ipa="ip -br a"
alias ima="date '+%Y-%m-%d-%H%M%S'"
alias count="wc -l"
alias nsp="netstat -plantu"

alias reg="grep -ir --color=always"
    # grep with pattern: `reg -e 'pattern'`, like `reg -e "test*"`
    # grep with regex: `reg -E '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'`, `reg -E '\bA_WORD\b|B_WORD'`
    # grep with full word match: `reg -w 'a_single_word'`
    # grep without binary file: `reg -I 'pattern'`

alias size="du -abh --time -d 1"
alias ssize="du -abh --time -d 1 | sort -h"
    # exclude file size under 1G: `size -t 1G`;
    # exclude reg files: `size --exclude=*backups*`;
    # sort by size: `size | sort -h`

alias rcp="rsync -avtz --progress"
    # use ssh option: `rcp -e "ssh -p 22000 -i ~/.ssh/id_rsa" src user@host:/path/to/dst`

alias transfer="sd search http.favicon.hash:-620522584"
    # refresh the cache: `transfer --d`

alias 7za="7z a -r -t7z -mx=9 -m0=lzma2 -mfb=273 -md=32m -ms=on -mhe=on"
    # zip with password: `7za -p<password> archive_name.7z [file1] [file2] ...`
    # unzip with password: `7z x -p<password> archive_name.7z`
    # specific uncompress output directory: `7z x -o<output_directory> archive_name.7z`
## end_alias_anchor
