

Buffers
    1. `:Buffers` 查看当前 buffer
    2. `:bn`、`bp`、`b[num]` 下一个 buffer、上一个 buffer、第 num 个 buffer

windows
    1. `ctrl + w + w` 快速切换下一个 windows
    2. `ctrl + w + v s c o`，快速垂直、水平、关闭、关闭其他
    3. 选项卡，`:tab[options]` new、next、first、last

insert mode
    1. `i`、`I`，在当前光标之前位置插入、在当前行首插入
    2. `a`、`A`，在当前光标之后位置插入、在当前行末插入
    3. `s`、`S`，删除当前光标所指字符并插入、删除当前行并输入
    4. `o`、`O`，在当前行的下方、上方插入新行
    5. `gi`、`gI`，从当前缓冲区上次结束输入模式的地方开始输入、在当前行的第一列的位置开始输入
    6. `ctrl + h w u`，分别在输入模式下删除：光标前一个字符、光标前一个单词、光标前直到行首所有内容
    7. 在输入模式下 `ctrl + x` 进入 x 模式，然后 `ctrl + y e` 分别向上、向下滚动页面
    8.  插入模式执行普通命令，进入 insert 时，左下角显示 *insert*，此时按下 `ctrl + o` 变成 *(insert)*，然后可以输入单个指令，例如 `k j h l`、`a A i I x X`、`!! pwd`、`zz H/M/L` 等

motions and operators，科技含量，kjhl，上下左右，`$ } w e b`
    1. `y$` yank from current to $，即复制从光标当前位置（光标前）开始直到行尾到剪贴板
    2. `dw` delete from current to next word，删除从当前位置开始到下一个 word
    3. `c}` change text from current to next paragraph，修改从当前位置开始到下一个段落的文本
    4. `y2h` yank 2 positions left from current，向左复制两个字符
    5. `d2w` delete 2 words from current，向后复制两个单词
    6. `c2j` change 2 lines，向下修改两行
    7. `d5G` delete from current line to line 5，将从本行开始到第 5 行的内容全部删除，可以向上也可以向下
    8. 重复 `dd`、`yy` 和 `cc` 分别代表 删除该行、复制该行、将该行剪切到寄存器并进入插入模式
    9. `24l`、`3w`、`5W`、`4B`，向右移动 24 次、向后移动 3 个 word、向后移动 5 个 WORD、向前移动 4 个 WORD 并将光标放在单词处
    10. `5k`、`7j`、`16G` 向上 5 行、向下 7 行、跳到第 16 行
    11. `fa`、`Fb`、`;`、`,` 当前行内向后跳到 a 字符处、当前行内向前跳到 b 字符处、重复上一个跳转、反向重复上一个跳转，将 `f` 改成 `t` 就是跳转后到达字符前
    12. 使用 `(`、`)` 跳转句子，`{`、`}` 跳转段落
    13. 使用 `gg`、`G`、`nG` 分别跳到第 1 行、最后 1 行、第 n 行
    14. 使用 `H`、`M`、`L` 分别跳转到当前窗口的顶部、中间、底部
    15. 知道文章大概在 70% 的位置，使用 `70%` 可以直接跳转
    16. `dta` delete to letter a，从当前位置开始，直到 a 之前的字符全部删除
    17. 例如使用 `/test` 匹配到 *test* 字符串，然后输入 `cwhello<esc>` 这一句是将 test 修改成 hello，然后退出插入模式，随后输入 `n` 进行下一个匹配，`.` 会自动重复 `cwhello<esc>` 的行为；像这样通过 `n.n.n.` 的方式即可实现 vscode 下的 `ctrl + h` 逐个替换
    18. 

netrw
    1. `:Explore` 打开文件浏览器，`:sexplore` 垂直、`:vexplore` 水平，
    2. `% [d]elete [R]ename [D]elete` 创建文件、创建目录、重命名、删除
    3. 

fzf，`:Files`，`ctrl + f`，`tab` 选中文件一起打开，单个 `enter` 则直接打开
    1. `^welcom` 前缀精确匹配，返回 *welcome*
    2. `down$` 后缀精确匹配，返回 *markdown*
    3. `'welcome to markdown` 表示整句精确匹配，返回 *welcome to markdown*
    4. `welcome | markdown` 表示 或 语法，尽可能返回 welcome 和 markdown
    5. `welcome !markdown` 表示 非 语法，返回不含 markdown 的 *welcome xxx* 短语

text object operate
    1. `di(`，`da(`，`( { < [`
    2. `di[option]`，[w]ord、[p]aragraph、[s]entence、[t]ag

scrol
    1. 使用 `zt`、`zz`、`zb` 将当前行置于屏幕：顶部、中央、底部

search
    1. 使用 `/xxx`、`?xxx`、`n`、`N` 实现搜索文本中的 xxx：向后、向前、重复上一个搜索、反向重复上一个搜索
    2. 使用 `/<\hello\>` 表示全词匹配，则单个 *hello* 会被匹配，但是 `hello_world` 就不会被匹配
    3. 使用 `*`、`#` 快速向前或向后搜索当前光标指向的文本的单词

marks
    1. 使用 `mx` 为当前光标位置设置一个标记，`x` 可以是 `a-zA-Z`，然后使用 \`x 跳转到 x 所在的精确位置（行和列），使用 `'x` 跳转到 x 所在的行；x 小写是文件内标签，X 大写是全局标签（也叫文件标签）
    2. 使用 `:marks` 查看所有标签
