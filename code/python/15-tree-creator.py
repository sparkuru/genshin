# -*- coding: utf-8 -*-

import json
import argparse

ap = argparse.ArgumentParser(description="传入 json 文件，生成树形结构")
ap.add_argument("-f", "--filepath", help="json 文件路径")
ap.add_argument("-e", "--example", action="store_true", help="显示示例")
ap.add_argument(
    "-m",
    "--make_example",
    action="store_true",
    help="生成一个 example 文件 tree-example.json",
)
args = vars(ap.parse_args())

banner = """1. 表示在同目录下，使用 [ file1, file2, dir1, dir2 ] 来界定
2. 表示某个目录下的子目录，使用 { "dir1": [] }
3. 组合以上内容，得到以下 json 文件：

    {
        "root": [
            {   # 表示一个文件夹 /root/diy/
                "diy": [    # 表示文件夹的子文件 /root/diy/*
                    "readme.md",
                    "unix-install-vim.sh",
                    "windows-vimrc"
                ]
            },
            "README.md",    # 表示文件 /root/README.md
            {
                "tutorials": [
                    "ch00_read_this_first.md",
                    "ch01_starting_vim.md",
                    "ch24_vim_runtime.md",
                    {   # 文件夹 /root/tutorials/images/*
                        "images": [
                            "diffing-apples.png",
                            "fugitive-git.png",
                            "session-layout.png"
                        ]
                    },
                    "LICENSE",
                    "readme.md"
                ]
            },
            {
                "write": [
                    "often.md",
                    "readme.md",
                    "tcpdump.py",
                    "test.md"
                ]
            }
        ]
    }

生成如下树形结构:
    root
    ├── diy
    │   ├── readme.md
    │   ├── unix-install-vim.sh
    │   └── windows-vimrc
    ├── README.md
    ├── tutorials
    │   ├── ch00_read_this_first.md
    │   ├── ch01_starting_vim.md
    │   ├── ch24_vim_runtime.md
    │   ├── images
    │   │   ├── diffing-apples.png
    │   │   ├── fugitive-git.png
    │   │   └── session-layout.png
    │   ├── LICENSE
    │   └── readme.md
    └── write
        ├── often.md
        ├── readme.md
        ├── tcpdump.py
        └── test.md

"""


def color(text: str = "", color: int = 2) -> str:
    color_table = {
        0: "{}",  # 无色
        1: "\033[1;30m{}\033[0m",  # 黑色加粗
        2: "\033[1;31m{}\033[0m",  # 红色加粗
        3: "\033[1;32m{}\033[0m",  # 绿色加粗
        4: "\033[1;33m{}\033[0m",  # 黄色加粗
        5: "\033[1;34m{}\033[0m",  # 蓝色加粗
        6: "\033[1;35m{}\033[0m",  # 紫色加粗
        7: "\033[1;36m{}\033[0m",  # 青色加粗
        8: "\033[1;37m{}\033[0m",  # 白色加粗
    }
    return color_table[color].format(text)


def print_tree(data, indent="", is_last=True):
    """
    递归打印树结构
    """
    if isinstance(data, dict):
        for idx, (key, value) in enumerate(data.items()):
            connector = "└── " if is_last and idx == len(data) - 1 else "├── "
            # key = key.replace("GREEN", "\033[1;32m").replace("EOC", "\033[0m")
            print(f"{indent}{connector}{key}")
            next_indent = indent + (
                "    " if is_last and idx == len(data) - 1 else "│   "
            )
            print_tree(value, next_indent, is_last=(idx == len(data) - 1))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            print_tree(item, indent, is_last=(idx == len(data) - 1))
    else:
        connector = "└── " if is_last else "├── "
        print(f"{indent}{connector}{data}")


def json_to_tree(json_data):
    """
    处理根节点并打印目录树
    """
    root_key = list(json_data.keys())[0]
    print(root_key)
    print_tree(json_data[root_key], indent="")


if args["example"] or args["make_example"]:
    if args["example"]:
        print(color(banner, 5))
    if args["make_example"]:
        with open("tree-example.json", mode="w+", encoding="utf-8") as fd:
            fd.write(
                """{
    "root": [
        {
            "diy": [
                "readme.md",
                "unix-install-vim.sh",
                "windows-vimrc"
            ]
        },
        "README.md",
        {
            "tutorials": [
                "ch00_read_this_first.md",
                "ch01_starting_vim.md",
                "ch24_vim_runtime.md",
                {
                    "images": [
                        "diffing-apples.png",
                        "fugitive-git.png",
                        "session-layout.png"
                    ]
                },
                "LICENSE",
                "readme.md"
            ]
        },
        {
            "write": [
                "often.md",
                "readme.md",
                "tcpdump.py",
                "test.md"
            ]
        }
    ]
}
                """
            )
    exit()

if not args.get("filepath", ""):
    print(color("lack of json file path, see `python tree-creator.py -h` for help", 4))
    exit(1)

with open(args["filepath"], "r", encoding="utf-8") as f:
    json_data = json.load(f)
    json_to_tree(json_data)
