if [ $# -ne 1 ]; then
    echo "usage: $0 <install|remove|no_proxy>"
    exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "run script with sudo"
    exit 1
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
    curl -fLo $1 --create-dirs $2
}

install_vim() {
    define_env
    echo "${GREEN}install vim${NC}"

    if [ ! -d $local_vim_root ]; then
        mkdir $local_vim_root
    fi

    ln -s $vim_dir/autoload $local_vim_root/autoload
    ln -s $vim_dir/colors $local_vim_root/colors

    mkdir -p $local_vim_tmp_dir
    chown -R $USER:$USER $local_vim_root

    _curl \
        $home_vimrc \
        https://raw.githubusercontent.com/shi9uma/vim/main/diy/unix-vimrc
    _curl \
        $local_vim_root/autoload/plug.vim \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    _curl \
        $local_vim_root/colors/gruvbox.vim \
        https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim
    
    vim -c PlugInstall -c qa
}

remove_vim() {
    define_env
    echo "${RED}remove vim${NC}"

    rm -rf $local_vim_root
    rm -rf $home_vimrc
}