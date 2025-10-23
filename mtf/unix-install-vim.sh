if [ $# -ne 1 ]; then
    echo "usage: $0 <install|remove>"
    exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "run script with sudo for first time"
fi

# color, usage: ${RED}xxx${NC}
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

define_env() {
    vim_root=/usr/share/vim
    vim_version_dir_name=$(ls $vim_root | grep '^vim[0-9]\{2\}$')
    vim_dir=$vim_root/$vim_version_dir_name
    local_vim_root=$HOME/.vim
    local_vim_tmp_dir=$local_vim_root/tmp
    home_vimrc=$HOME/.vimrc
}

_curl() {
    if [ -f $1 ]; then
        return
    fi
    echo "file ${CYAN}${1}${NC} not found, download from ${CYAN}${2}${NC} (need sudo)"
    sudo curl --create-dirs -fLo $1 $2
}

install_vim() {
    define_env
    echo "${GREEN}installing vim${NC}"

    if [ ! -d $local_vim_root ]; then
        mkdir $local_vim_root
    fi

    if [ ! -d $local_vim_root/autoload ]; then
        ln -s $vim_dir/autoload $local_vim_root/autoload 2>/dev/null
    fi
    if [ ! -d $local_vim_root/colors ]; then
        ln -s $vim_dir/colors $local_vim_root/colors 2>/dev/null
    fi

    echo "${CYAN}\$USER = $USER${NC}"

    mkdir -p $local_vim_tmp_dir

    _curl \
        $home_vimrc \
        https://raw.githubusercontent.com/sparkuru/vim/main/diy/unix-vimrc 2>/dev/null
    _curl \
        $local_vim_root/autoload/plug.vim \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim 2>/dev/null
    _curl \
        $local_vim_root/colors/gruvbox.vim \
        https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim 2>/dev/null

    vim -c PlugInstall -c qa
    chown -R $USER:$USER $local_vim_root
}

remove_vim() {
    define_env
    echo "${RED}remove vim${NC}"

    rm -rf $local_vim_root
    rm -rf $home_vimrc
}

if [ $1 = "install" ]; then
    install_vim
elif [ $1 = "remove" ]; then
    remove_vim
fi
