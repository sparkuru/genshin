# markdown-template

> 记录个人使用 markdown 的写作习惯，格式等的模板内容

简体中文 | [English](./如果有的话)

## 项目介绍 | Introduction

一段话简单介绍内容。

* 陈列内容1
* 陈列内容2
* 陈列内容3

## 特性 | Feature

TODO list 方式

* [X] 特性1
* [ ] 特性2
* [ ] 特性3

---

也可用图表对比的方式（多用于修改）

| xxx | xxx | xxx |
| ----- | ----- | ----- |
| sth | √  | ×  |
| sth | √  | ×  |
| sth | √  | ×  |

## 可选内容（应当至少一项） | Options

* 使用方法 | Usage
* 部署方法 | Install
* 效果图 | Snapshot
* 更新记录 | Update

  ```markdown
  ** year - month - day **
  1. 更新了 xxx
  2. 更新了 xxx
  ```
* 致谢信息 | Acknowledgment
* 联系本人 | Contact
* ...

## 写作语法 | Typesetting

下面列出正常写作内容中会使用到的语法

### 文本规定语法

1. `文件路径`，`按键组合`，`command_line`
2. **重要提示**，*命令输出内容*
3. 中英文间需要 space
4. ~~后期修改的内容，需要删除的内容，吐槽等~~
5. 代码块

    ```python
    print("Hello, World")
    ```
6. 符号使用

    1. 英文半角符号 `,` 后面需要空一格，写代码中遇到中文注释的地方要英文半角，但是确定要输出的内容用全角
    2. 中文全角符号 `，` 后面直接写内容，写文章主要用全角，遇到代码块等逻辑用半角
7. 下划线与中划线

    1. 不要用驼峰法（除非团队明确要这么做），适应 unix，使用全小写，并以分隔符分开
    2. 当不会被编程项目使用、引入时，项目名称、文章标题用 `-` 连接，例如：`markdown-template`
    3. 当会被编程项目使用、引入时，文件（夹）名称、单词之间使用 `_` 来连接，文件排序命名：`01_dir_01`，基本逻辑是用 `_` 代替空格
    4. 一些语言环境解析在使用以上两者都有可能非法：

        1. 语言在 import 或者 include 等时，应该使用 `package_package`
        2. latex 语法在引入源文件时不能使用下划线 `_`

    总结，具体环境具体分析，非编程项目的文件夹 `01-dir-aa-bb-cc`，文件 `02-file02-info01-info02.filetype`；在编程项目中才使用下划线 `import 01_code_aa_bb/package_name`
8. 公式

    1. 单行公式 $E = mc^2$

        ```markdown
        ‍```latex
        E = mc^2
        ‍```
        ```
    2. 多行公式

        $$
        \begin{align*}
        g(x, y) &= f(x, y) \times h(x, y) \tag1 \\
        &= \underset {(m,n) \in S} {\sum\sum} h(m,n) f(x-m, x-n) \tag2 \\
        &= \underset {(m,n) \in S} {\sum\sum} f(m,n) h(x-m, x-n) \tag3
        \end{align*}
        $$

        ```latex
        \begin{align*}
        g(x, y) &= f(x, y) \times h(x, y) \tag1 \\
        &= \underset {(m,n) \in S} {\sum\sum} h(m,n) f(x-m, x-n) \tag2 \\
        &= \underset {(m,n) \in S} {\sum\sum} f(m,n) h(x-m, x-n) \tag3
        \end{align*}
        ```

### 文本写作格式

正常写作换行：单个 `Enter`

---

## <center>居中内容</center>

---

<div>
<p align = "right">右对齐内容</p>
</div>

```markdown
## <center> 居中内容 </center>
<p align = "right"> 右对齐内容 </p>
```

### 导航栏

[TOC]

```markdown
[TOC]
```

### 引用与解释

> 写上文字引用

```markdown
> 写上文字引用
```

> 或者是提出问题

回答内容

### 链接

图片链接：![图片介绍](图片链接url)

链接：[链接标识](链接url)

文章内跳转：[页面内目标内容](#引用与解释)

## 参考链接 | References

1. [Markdown-Pastebin](https://rentry.co/)
2. [typora-theme-redrail](https://github.com/airyv/typora-theme-redrail/blob/main/README.md)
3. [文件命名，下划线还是中划线？](https://adoyle.me/Today-I-Learned/others/file-naming-with-underscores-and-dashes.html)