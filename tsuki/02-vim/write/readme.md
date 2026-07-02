# learn vim
### chapter 0
1. `:h :help cmd` 查看具体命令，特别的如果想查看 insert 状态下某个命令，应该是 `:h i_cmd`
2. `:w` 直接保存，但是 `:w :write new_file_name.txt` 会将其另存为
3. 一些指令并不需要记得很清楚，不记得了就 `:h cmd`，并且使用 `tab` 自动补全

### chapter 1
4. 当通过 `vim file1 file2` 打开多个文件时，使用 `:buffer :b filex` 来切换不同文件
5. vim 支持打开文件后立即执行 cmd，例如 `vim file +version` 以及 `vim +version file` 则使用 vim 打开文件 file 后将自动执行 `:version` 指令；还可以使用 `vim -c version file` 来代替 `+` 号
6. `:substitue :s` 用于替换文本，基本表达式如下：`:[范围]s/被替换值（或正则表达式）/替换值/[flag]`，后续第 12 章会有详细介绍
7. 打开多个窗口：`vim -o5 file1 file2` 用于打开 5 个水平分割的窗口，`vim -O2` 大写的用于打开 2 个垂直分割的窗口，打开窗口可以用鼠标点击来切换工作窗口
8. 在 unix 下可以通过 `ctrl + z`、`:suspend`、`:stop` 直接挂起当前 vim 编写进程，使用 `fg` 可以恢复该进程

### chapter 2
9. 接 4，输入 `:buffers :ls :files` 可以查看当前打开的所有 buffer，输入 `:buffer filename` 或 `:buffer 文件对应编号num` 可以打开对应文件，也可以使用快捷指令 `:bp :bprevious` 或者 `:bn :bnext` 快速切换上下文件；输入 `:bdelete` 来删除当前 buffer，如果指定了数字或者文件名则删除对应 buffer
10. vim 的 buffers 设计是为了一次性修改多个文件，可以通过 `:wqall` 来保存并退出所有 buffer
11. `:split` 主要的作用是创建 windows，当已经打开了一个文件时，此时再 `:split <filename>` 即可将当前 terminal 分割成上下两个窗口，并在另一个窗口显示 filename 的内容，如果不指定文件名就是将当前 buffer 分割两个 windows，`:vsplit` 对应左右两个窗口
12. `crtl + w + H J K L`，这里的 w 就是 windows，用于直觉地切换不同的窗口（但是由于自己设置了 `ctrl + w` 等于关闭当前终端，因此该方式对 vim 无效，但是对 gvim 有效），还可以选择通过 mouse 来切换窗口；`ctrl + w [options]`，v 打开一个新的垂直窗口、s 打开新的水平窗口、c 关闭当前窗口、o 关闭除了当前窗口以外所有的窗口
13. `:tabnew filename`，就是新开一个选项卡并装载 filename，类似的还有：`:tabclose` 关闭当前 tab，`:tabnext :tabpreview :tablast :tabfirst` 下一个、前一个、最后一个、第一个 tab 选项卡；如果想让 vim 在启动时打开多个选项卡，则 `vim -p file1 file2 file3`

### chapter 3
14. `:edit filename` 用于编辑文件，如果文件不存在，则会新建之，也可以 tab 自动列出所有文件然后选择之；`:edit *.md`，然后 tab 即可自动列出所有 .md 的文件供选择；`:edit **/*.md` 然后 tab 可以递归当前目录下所有文件找到这些 .md 文件；如果只是 `:edit .` 传入目录，则将启动 netrw，即 vim 自己的文件浏览器，然后可以选择目录和文件
15. `:find` 指令主要用于根据 `:set path?` 所返回的路径进行查找，一般来说会引入特定的环境变量，例如引入 **/usr/include** 可以查找 c 编译器头文件目录，则执行 `:find filename` 后可以在这些目录下进行查找；添加新的 path 可以按照这个方法：`:set path+=/path/want/to/add`，在进行一些大的项目开发时，可以按照 `:set path+=$PWD/**` 的方法将整个项目的路径引入，这样在 find 时可以找到想要的文件了
16. grep 查找内容，有两种方式：`:vim :vimgrep` 是 vim 内置的 grep，而 `:grep` 是外置的 grep，基本语法与 `grep --help` 的语法一致，即 `grep /pattern/ filename`，这样会打开一个 quickfix 窗口，主要有有以下命令: `:copen :cclose :cnext :cprevious`
17. vim 内置文件浏览器 netrw，主要有以下用法：`:Explore` 直接打开浏览器，`:Sexplore` 打开一个垂直窗口文件浏览器，`:Vexplore` 打开一个水平窗口文件浏览器；在 netrw 中有几个命令：`%` 创建新文件、`d` 创建新目录、`R` 重命名文件或目录、`D` 删除文件或目录
18. fzf，一个通用的模糊匹配器，参照 diy/readme.md 安装插件，安装完成后输入 `:Files` 可以获取到该指令，以下是 fzf 的基础语法：
    1. `^welcom` 前缀精确匹配，返回 *welcome*
    2. `down$` 后缀精确匹配，返回 *markdown*
    3. `'welcome to markdown` 表示整句精确匹配，返回 *welcome to markdown*
    4. `welcome | markdown` 表示 或 语法，尽可能返回 welcome 和 markdown
    5. `welcome !markdown` 表示 非 语法，返回不含 markdown 的 *welcome xxx* 短语
19. 搭配以上插件进行搜索并替换，`<leader>bd`（自定义的按键映射，原理是 `:bufdo bd |e#`）关闭所有 buffer，然后重新打开当前 buffer，`ctrl + f` 使用 fzf 的 <tab> 选择要打开的 buffer，然后 `:buffer %s/被替换/替换值/g | update` 一次性将所选的 buffer 中的指定值进行替换

### chapter 4
20. motion，vim 中的动作，有点反人类：
    1. k，上
    2. j，下
    3. h，左
    4. l，右
        上下左右，科技含量，kjhl
    5. w，下一个单词 word
    6. }，下一个段落
    7. $，行尾
    8. e，下一个单词的结尾
    9. b，上一个单词的开始
21. operator，操作符
    1. y，yank 复制
    2. p，paste 粘贴，`P` 大写的是光标前的，`p` 小写的是光标后的，这和许多操作符的前后逻辑类似
    3. d，delete 删除
    4. c，change 原意是修改文本，表现为删除选中文本，将其存入寄存器，后续可以用 `p` 粘贴
22. 组合技，例如有
    1. `y$` yank from current to $，即复制从光标当前位置（光标前）开始直到行尾到剪贴板
    2. `dw` delete from current to next word，删除从当前位置开始到下一个 word
    3. `c}` change text from current to next paragraph，修改从当前位置开始到下一个段落的文本
    4. `y2h` yank 2 positions left from current，向左复制两个字符
    5. `d2w` delete 2 words from current，向后删除两个单词
    6. `c2j` change 2 lines，向下修改两行
    7. `d5G` delete from current line to line 5，将从本行开始到第 5 行的内容全部删除，可以向上也可以向下
    8. `dta` delete to letter a，从当前位置开始，直到 a 之前的字符全部删除
    另外，重复 `dd`、`yy` 和 `cc` 分别代表 删除该行、复制该行、将该行剪切到寄存器并进入插入模式
23. 文本对象操作：i 表示区域内部、a 表示整个区域，假设有以下代码块
    ```javascript
    const hello = function() {
        console.log("Hello Vim");
        return ture;
    }
    ```
    将光标放在 Hello 的 H 处，`di(` 将自动定位 *"Hello Vim"* 然后将其 delete，如果是 `da(` 则删除整个 *("Hello Vim")*，同理还有 `di{` 删除整个 `{}` 里的内容，`diw` 删除 *Hello* 这个单词
    假设又有以下代码块：
    ```html
    <div>
        <h1>header1</h1>
        <p> para1 </p>
        <p> para2 </p>
    </div>
    ```
    将光标放置于 header1 的 h，输入 `dit` 则删除整个 *header1*，输入 `dat` 删除 *\<h1>header1\</h1>*
    将光标放置于 div 处，`dit` 将删除 *\<div>\</div>* 内所有的 h1 和 p，`dat` 将额外删除 div 整个模块，如果是 `di<` 则删除 *div* 这三个字符（和上文的 `di(` 逻辑类似）
    输入 `:h text-object` 获取更多帮助，以下是常见的文本对象：`[w]ord`、`[p]aragraph`、`[s]entence`、`(`、`{`、`[`、`<`、`t` 代表 xml 标签、`"`、`'`
24. vim motion 和 operator 与 unix 命令结合
    假设有以下文本：
    
    ```
    1234
    abcd
    Id|Name|Age
    1|Alice|20
    2|Bob|22
    3|Caddy|19
    23212421
    asdasca
    ```
    将光标放在 Id 处，然后输入 `!}column -t -s "|"`：`!` 的作用可以理解为一个占位符，用于表示后面的指令；`}` 用于标识命令操作的对象范围，即到下一个段落；`column -t -s "|"` 是 unix 上的指令，用于通过 "|" 标识来将数据 table 化。以上指令就是相当于将 `!` 修改成 `column -t -s "|"`，然后作用范围是整个段落，结果如下：
    ```
    1234
    abcd
    Id      Name   Age
    1       Alice  20
    2       Bob    22
    3       Caddy  19
    23212421
    asdasca
    ```
    像这样，通过 motion 和 operator 相结合：motion 到哪个位置，operator 做什么事，实现强大的文本编辑，更何况 `!` 允许调用更多的 unix 指令实现更好的文本处理。以下是引用原文：
    
    > 你知道的动词 **操作符**，名词 **动作**，终端命令越多，你组建复杂操作的能力成倍增长。
    >
    > 换句话说，假设你只知道四个 **动作**：`w, $, }, G` 和删除操作符 `d`，你可以做 8 件事：按四种方式移动 `w, $, }, G` 和删除 4 种文本对象 `dw, d$, d}, dG`；如果有一天你学习了小写变大写的 **操作符** `gU`，你的 Vim 工具箱中多的不是 1 种工具，而是4种：`gUw, gU$, gU}, gUG`，现在你的 Vim 工具箱中就有12种工具了；如果你知道 10 个 **动作** 和 5 个 **操作符**，那么你就有 60 种工具：50 个操作 + 10 个移动。另外，行号动作 `nG` 给你了 `n` 种 **动作**，其中 `n` 是你文件中的行数：例如前往第 5 行 `5G`。搜索动作 `/` 实际上给你带来无限数量的 **动作** 因为你可以搜索任何内容。你知道多少终端命令，外部命令操作符 `!` 就给你了多少种过滤工具。使用 Vim 这种能够组合的工具，所有你知道的东西都可以被串起来完成更复杂的操作。你知道的越多，你就越强大。
    >
    > 这种具有结合性的行为也正符合 Unix 的哲学：*一个命令做好一件事*。**动作** 只需要做一件事：前往 X。**操作符** 只需要做一件事：完成 Y。通过结合一个 **操作符** 和一个 **动作**，你就获得了 YX：在 X 上完成 Y。

### chapter 5
25. 为什么 Vim 使用 `hjkl` 进行移动，*这实际上是因为 Bill Joy 写 VI 用的 Lear-Siegler ADM-3A 终端没有方向键，而是把 `hjkl` 当做方向键*
    1. 使用 `[num][motion]` 来实现快速执行 num 次 motion，例如 `12l` 则向右移动 12 次，`6j` 则向下移动 6 line，`7k` 向上移动 7 line；在 vimrc 中设定 `set relativenumber` 可以开启相对行号，可以直接看到其他行相对于当前行的距离，当然也可以使用 `16G` 直接跳转到第 16 line
    2. 词组（WORD），相对于单词（word）。二者的区分在于，单词指的是一个只包含 `a-zA-Z0-9` 的字符串，遇到不同类型的就会被视作两个单词；但是一个词组使用 space、tab、EOL 进行分割，参照以下内容：
    ```
    const WORD = "Hello_Vim";
    ```
    将光标放在段落首的 c 处，需要 `24l` 才可以到段尾，`6w` 到段尾，而只需要 `4W` 到段尾
26. 当前行导航：
    1. 当前行内导航有以下操作：`0`、`^`、`g_`、`$`、`n|` 分别表示跳到本行：第 1 个字符、第一个非空字符、最后一个非空字符、最后一个字符、第 n 列
    2. 当前行内检索（也可以视作根据检索词跳转）：`f`、`F`、`t`、`T`、`;`、`,` 分别表示在本行：向后搜索、向前搜索、向后搜索、向前搜索、重复近一次搜索、相反方向地重复近一次搜索，即大写向前，小写向后，`fF` 是定位到那个字符，`tT` 是定位到那个字符前；例如 `Ft` 会跳转到当前行前边的 *`tT`* 处
27. 句子和段落的跳转
    1. 将 `.!?` 跟着一个 `\n`、`space` 或 `<tab>` 之前的字符集合定为一个句子，使用 `(` 和 `)` 分别跳转到上一个和下一个句子的开头
    2. 一个段落以一个空行作为开始和结尾，使用 `{`、`}` 跳转上下一个段落
28. 匹配导航，有以下代码块：
    ```
    (define (fib n)
      (cond ((= n 0) 0)
            ((= n 1) 1)
            (else
              (+ (fib (- n 1)) (fib (- n 2)))
            )))
    ```
    使用 `%` 可以快速匹配一对括号，还可以安装插件 [vim-rainbow](https://github.com/frazrepo/vim-rainbow) 增强文章中的括号体验
29. 行号导航
    1. 使用 `gg`、`G`、`nG` 跳转到第一行、最后一行、第 n 行
    2. 不清楚要跳转到具体的行号，但是知道大概在文章 70% 的位置，使用 `70%` 可以直接跳转
    3. 可以使用 `ctrl + g` 查看文件总共有多少行
30. 窗格导航
    1. 根据窗口跳转，使用 `H`、`M`、`L` 分别跳转到当前窗口的顶部、中间、底部，大概跳转到这些地方，但是具体的跳转结果通过 `:help H` 进行参考
    2. 输入 `nH`、`nL` 跳转到举例顶部、底部 n 行的位置
31. 窗口滚动
    1. 使用 `ctrl + b`、`ctrl + f` 向上下滚动一个屏幕，不过由于 `ctrl + f` 被 fzf 注册了，建议使用下面的指令
    2. `zt`、`zz`、`zb` 将当前行置于屏幕：顶部、屏幕中央、屏幕底部
32. 搜索导航
    1. 使用 `/xxx`、`?xxx`、`n`、`N` 实现搜索文本中的 xxx：向后、向前、重复上一个搜索、反向重复上一个搜索
    2. 使用 `/<\hello\>` 表示全词匹配，则单个 *hello* 会被匹配，但是 `hello_world` 就不会被匹配
    3. 例如有 `hello vim, hello vim2, hello_vim`，将光标放在句子首部，使用 `*`、`#` 快速向前或向后搜索当前光标指向的文本的单词 hello，如果使用 `g*`、`g#` 则会匹配到 *hello_vim*
33. 位置标记导航
    1. 使用 `mx` 为当前光标位置设置一个标记，`x` 可以是 `a-zA-Z`，然后使用 \`x 跳转到 x 所在的精确位置（行和列），使用 `'x` 跳转到 x 所在的行；x 小写是文件内标签，X 大写是全局标签（也叫文件标签）
    2. 使用 `:marks` 查看所有标签

### chapter 6
34. 进入输入模式的方法
    1. `i`、`I`，在当前光标之前位置插入、在当前行首插入
    2. `a`、`A`，在当前光标之后位置插入、在当前行末插入
    3. `s`、`S`，删除当前光标所指字符并插入、删除当前行并输入
    4. `o`、`O`，在当前行下方、上方新起一行输入，主要是搭配后面的快速输入达到多行插入的效果
    5. `gi`、`gI`，从当前缓冲区上次结束输入模式的地方开始输入、在当前行的第一列的位置开始输入
35. 输入模式下删除，在输入模式下通过以下快捷键
    1. `ctrl + h`，删除光标前一个字符
    2. `ctrl + w`，删除光标前一个单词
    3. `ctrl + u`，删除光标前直到行首所有内容
36. 寄存器模式，可以将目标存储和取出于寄存器中
    1. `"ayiw`，`"a` 告知将要把后面的操作存放到寄存器 a 中，`yiw` 表示复制（[y]ank）一个单词（[i]nner [w]ord），组合起来就是将 yiw 操作的结果存放到 a 里
    2. 使用 `ctrl + r a` 即可将 a 里的内容粘贴出来
37. 输入模式滚动，在输入模式下，`ctrl + x` 进入 x 模式，然后 `ctrl + y e` 分别向上、向下滚动页面
38. 插入模式执行普通命令，进入 insert 时，左下角显示 *insert*，此时按下 `ctrl + o` 变成 *(insert)*，然后可以输入单个指令，例如 `k j h l`、`a A i I x X` 等
    1. `ctrl + o !! pwd` 执行 `pwd` 指令并插入到当前光标位置
    2. `ctrl + o zz H/M/L` 进行窗口位置的调整
    3. `ctrl + o dta yta` 从当前位置开始直到 a 全部删除、复制

### chapter 7
39. 点命令，重复上一个修改 buffer 的操作
    1. 例如使用 `/test` 匹配到 *test* 字符串，然后输入 `cwhello<esc>` 这一句是将 test 修改成 hello，然后退出插入模式，随后输入 `n` 进行下一个匹配，`.` 会自动重复 `cwhello<esc>` 的行为；像这样通过 `n.n.n.` 的方式即可实现 vscode 下的 `ctrl + h` 逐个替换；当然还有一条指令：`cgnhello<esc>` 用于快速、可视化地进行替换，并且不再需要按 `n`，而是自动地跳转到下一个 `test`
    2. 例如有以下代码块：
    ```
    zlet zzone = '1';
    zlet zztwo = '2';
    zlet zzthree = '3';
    zlet zzfour = '4';
    ```
    光标放在第一个 z 上，输入 `ctrl + v3jd`，会将开头的 z 全部删除，然后按下 `w` 会跳转到第 6 列，此时再 `.` 即可自动重复 `ctrl + v3jd`，最终只需要输入 `ctrl + v3jdw.w.` 即可实现

### chapter 8
40. 接 36，继续描述寄存器模式
    1. 
