# diy

## windows

在 windows powershell in terminal 下 portable 使用 vim、gvim 为目的，并集成插件

1. 获取 [vim](https://www.vim.org/download.php) 的 portable 文件，解压到 `d:/bin/vim` 目录下备用，后文给出项目具体目录拓扑

2. 将 vim 的 binary 路径添加到 powershell 的配置文件 `$profile` 中，参考如下：

   ```powershell
   $VIMPATH = "d:/bin/vim/vim90"
   $env:PATH += ";$VIMPATH"
   ```

3. 配置 vim 的几个路径，这里是根据传统单个 windows 下只有 user 和 administrator 两个账户来配置，也就是说默认这台 pc 只有你自己用，如果是多账户模式，那就默认配置吧，多账户电脑建议用 unix

   1.   首先查看 vim 的配置文件目录 `vim --version`，可以得到以下输出：

        ```bash
             系统 vimrc 文件: "$VIM/vimrc"
             用户 vimrc 文件: "$HOME/_vimrc"
         第二用户 vimrc 文件: "$HOME/vimfiles/vimrc"
         第三用户 vimrc 文件: "$VIM/_vimrc"
              用户 exrc 文件: "$HOME/_exrc"
          第二用户 exrc 文件: "$VIM/_exrc"
               defaults 文件: "$VIMRUNTIME/defaults.vim"
        ```

   2.   创建通用配置文件：`touch d:/bin/vim/vimrc`，添加以下内容：

        ```ini
        ...
        
        set encoding=UTF-8
        
        " 修改 windows 下备份、撤销、临时文件的目录
        set backupdir=d:/bin/vim/tmp
        set undodir=d:/bin/vim/tmp
        set directory=d:/bin/vim/tmp
        
        let $configs_dir = "d:/bin/vim/configs"
        let $vim_base_dir = "d:/bin/vim"
        let $vim_runtime_dir = "d:/bin/vim/vim90"
        
        let $VIM = $vim_base_dir
        let $HOME = $configs_dir
        let $VIMRUNTIME = $vim_runtime_dir
        
        ...
        ```

        1.   viminfo，\_viminfo 是单个用户启动时的操作备份，记录每个文件打了什么指令，将其全部修改成 `d:/bin/vim/configs/_viminfo`；`$home`，这个就是 unix 每个用户的 `~` 目录，在 windows 下对应 `C:/User/user/`，由于其影响到生成 viminfo、\_viminfo 的路径，因此需要将其在 vim 中修改而又不影响到系统变量
        2.   `$vim`，即 `d:/bin/vim`
        3.   `$vimrc`，vim 启动时读取的 rc 文件，即 `d:/bin/vim/configs/_vimrc`，这里强制指定 user 和 admin 都使用同一个 _vimrc 文件
        4.   `$myvimrc`，单个用户对应的 rc 文件，也改成 `d:/bin/vim/configs/_vimrc`
        5.   `$VIMRUNTIME`，就是 vim binary 所在的目录，即 `d:/bin/vim/vim90`

4. 顺便修改一下 git 默认的 vim 路径，否则又跑去 `$HOME` 生成文件了：`$env:GIT_EDITOR = "d:/bin/vim/vim90/vim.exe"`

5. vim 增强套件，适用于 windows 下的 `d:/bin/vim/vim90`

   1.   配色，参考于 [morhetz/gruvbox](https://github.com/morhetz/gruvbox.git)

        1.   `curl -o d:/bin/vim/vim90/colors/gruvbox.vim https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim`
        2.   `curl -o d:/bin/vim/vim90/autoload/gruvbox.vim https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim`
        3.   `curl -o d:/bin/vim/vim90/autoload/airline/themes/gruvbox.vim https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/airline/themes/gruvbox.vim`
        4.   `curl -o d:/bin/vim/vim90/autoload/lightline/colorscheme/gruvbox.vim https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/lightline/colorscheme/gruvbox.vim`

   2.   vim 插件管理工具，[junegunn/vim-plug](https://github.com/junegunn/vim-plug.git)：`curl -fLo d:/bin/vim/vim90/autoload/plug.vim https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim`，然后打开将以下基本语句写入到 `d:/bin/vim/vimrc` 末尾（参考）：

        ```bash
        " 开始声明
        call plug#begin('d:/bin/vim/plugins/')	" 指定插件安装目录
        
        " 开始获取插件
        Plug 'junegunn/fzf', {'do': { -> fzf#install() }}
        
        " 结束声明
        call plug#end()
        ```

        安装插件：`vim -c PlugInstall`

   3.   完成 2 后，安装以下插件：

        1.   vim 命令增强，模糊查找器，通过输入模糊的关键词就可以定位文件或文件夹，[junegunn/fzf.vim](https://github.com/junegunn/fzf.vim.git)，获取其 binary 文件放到 `d:/bin/fzf` 下
        2.   类 grep 工具，[BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep.git)，但不是插件，在 unix 下可以通过包管理器简易安装，在 windows 下通过 binary portable 使用，在 [release](https://github.com/BurntSushi/ripgrep/releases) 获取对应版本的 binary 文件，放到 `d:/bin/ripgrep` 文件夹，输入 `rg -h` 可以看到回显
        3.   括号高亮工具，[frazrepo/vim-rainbow](https://github.com/frazrepo/vim-rainbow.git)，`Plug 'frazrepo/vim-rainbow'`

        相关的 `$profile` 应该这么写：

        ```powershell
        $FZFPATH = "d:/bin/fzf"
        $RIPGREPPATH = "d:/bin/ripgrep"
        
        $env:PATH += ";$FZFPATH;$RIPGREPPATH"
        $env:FZF_DEFAULT_COMMAND = "rg --files"
        $env:FZF_DEFAULT_OPTS = "-m --height 40% --reverse --border --ansi"
        ```

        `d:/bin/vim/vimrc` 插件相关这么写：

        ```bash
        call plug#begin('d:/bin/vim/plugins')
        Plug 'junegunn/fzf.vim'	" 这个是联动 vim 和 fzf 的插件
        Plug 'junegunn/fzf', {'do': { -> fzf#install() }}
        Plug 'frazrepo/vim-rainbow'	" 括号高亮
        call plug#end()
        ```

6. 快速配置：`curl -fLo d:/bin/vim/vimrc https://raw.githubusercontent.com/shi9uma/vim/main/diy/windows-vimrc`

   1.   其中，在 terminal 下的 vim 的光标显示方法，[参考](https://rollingstarky.github.io/2021/06/08/change-vim-cursor-shape-and-color-in-xterm-or-windows-terminal/)


## unix

```shell
#/usr/bin/env zsh

sudo apt install vim fzf ripgrep

curl -fLo /tmp/unix-install-vim.sh https://raw.githubusercontent.com/shi9uma/vim/main/diy/unix-install-vim.sh
chmod +x /tmp/unix-install-vim.sh
/tmp/unix-install-vim.sh
```

## references

1.   [A basic .vimrc file that will serve as a good template on which to build.](https://gist.github.com/simonista/8703722)