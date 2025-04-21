# -*- coding: utf-8 -*-

# ============================== cli 传参 ============================== #
import argparse

ap = argparse.ArgumentParser()
ap.add_argument(
    "-d",
    "--dir",
    nargs="?",
    default="./",
    type=str,
    help="参数(简写), 参数(全称), 参数个数 0 或 1, 默认值, 类型, 帮助内容",
)
ap.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="参数(简写), 参数(全称), 行为(添加则转变为 ture), 帮助",
)
ap.add_argument("foobar", help="必要的参数")
args = vars(ap.parse_args())

args["dir"]  # 取值


class CLIStyle:
    """CLI 工具统一样式配置"""

    COLORS = {
        "TITLE": 7,  # 青色 - 主标题
        "SUB_TITLE": 2,  # 红色 - 子标题
        "CONTENT": 3,  # 绿色 - 普通内容
        "EXAMPLE": 7,  # 青色 - 示例
        "WARNING": 4,  # 黄色 - 警告
        "ERROR": 2,  # 红色 - 错误
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """统一的颜色处理函数"""
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


class ColoredArgumentParser(argparse.ArgumentParser):
    """统一的命令行参数解析器"""

    def _format_action_invocation(self, action):
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(
                    map(
                        lambda x: CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"]),
                        action.option_strings,
                    )
                )
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(
                        CLIStyle.color(
                            f"{option_string} {args_string}",
                            CLIStyle.COLORS["SUB_TITLE"],
                        )
                    )
            return ", ".join(parts)

    def format_help(self):
        formatter = self._get_formatter()

        # 添加描述
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )

        # 添加用法
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # 添加参数组
        formatter.add_text(
            CLIStyle.color("\nOptional Arguments:", CLIStyle.COLORS["TITLE"])
        )
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # 添加示例和注释
        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
    """创建统一的示例文本
    Args:
        script_name: 脚本名称
        examples: 示例列表，每个元素是 (描述, 命令) 的元组
        notes: 注意事项列表
    """
    text = f"\n{CLIStyle.color('示例:', CLIStyle.COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += (
            f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}"
        )
        text += "\n"

    if notes:
        text += f"\n{CLIStyle.color('注意事项:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


# ============================== misc ============================== #
def exec(cmd: str, print_output=False):
    """
    直接传入命令行字符串，执行命令行并返回输出和返回码
    ```python
    output, ret_code = exec('ls -l')
    output, ret_code = exec('ls -l', print_output=True)
    ```
    """
    assert type(cmd) == str, "wrong cmd"
    import subprocess

    try:
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        output = result.stdout
        ret_code = result.returncode

        if print_output:
            print(output)

        return ret_code, output
    except subprocess.CalledProcessError as e:
        if print_output:
            print(f"cmd exec failed: {e}")
        return e.returncode, e.output


def debug(*args, file=None, append=True, **kwargs):
    """
    打印传入的参数值，并显示其在源码的文件和行号

    参数:
        *args: 要打印的参数
        file: 输出文件路径，默认为None（输出到控制台）
        append: 是否追加到文件，默认为True
        **kwargs: 要打印的键值对参数
    """
    import inspect

    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)

    output = f"{color(clean_path(info.filename), 3)}: {color(info.lineno, 4)} {color('|', 7)} "

    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, 2)} "

    for k, v in kwargs.items():
        output += f"{color(k + '=', 6)}{color(str(v), 2)} "

    output += "\n"

    if file:
        mode = "a" if append else "w"
        with open(file, mode) as f:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            f.write(clean_output)
    else:
        print(output, end="")


def color(text: str = "", color: int = 2) -> str:
    """
    返回对应的控制台 ANSI 颜色;
    ```python
    color_table = {
        0: '无色',
        1: '黑色加粗',
        2: '红色加粗',
        3: '绿色加粗',
        4: '黄色加粗',
        5: '蓝色加粗',
        6: '紫色加粗',
        7: '青色加粗',
        8: '白色加粗',
    }
    ```
    """
    color_table = {
        0: "{}",
        1: "\033[1;30m{}\033[0m",
        2: "\033[1;31m{}\033[0m",
        3: "\033[1;32m{}\033[0m",
        4: "\033[1;33m{}\033[0m",
        5: "\033[1;34m{}\033[0m",
        6: "\033[1;35m{}\033[0m",
        7: "\033[1;36m{}\033[0m",
        8: "\033[1;37m{}\033[0m",
    }
    return color_table[color].format(text)


# ============================== path ============================== #
def clean_path(path: str) -> str:
    """
    清理反斜杠
    """
    return path.replace("\\", "/").lower()


def get_dirname(path: str) -> str:
    """
    返回路径的目录名
    """
    import os

    return clean_path(os.path.dirname(path))


def get_fullpath(path: str) -> str:
    """
    返回路径的绝对路径
    """
    import os

    return clean_path(os.path.abspath(path))


def get_workdir() -> str:
    """
    返回根工作目录
    """
    return get_fullpath(get_dirname(get_dirname(__file__)))


def xpath(root_path: str, *args: str) -> str:
    """
    将所有传入的参数按顺序组合成路径
    """
    import os

    for path in args:
        if type(path) != str:
            if type(path) == int:
                path = str(path)
            else:
                continue
        path = path.replace("\\", "").replace("/", "")
        root_path = os.path.join(root_path, path)
    return clean_path(root_path)


# ============================== split line ============================== #
SWITCH = {
    1: "-",
    2: "=",
    3: "✩",
}


def fgx(text="分割线", type=1, length="50", isPrint=True):
    text = " " + text + " "
    # print("{:=^60s}".format('分割线'))
    fmt = "\033[1;33m {:type^lengths} \033[0m".replace("length", length)

    if type not in SWITCH.keys():
        type = 1
    fmt = fmt.replace("type", SWITCH.get(type))

    if isPrint:
        print(fmt.format(text))
        return None
    else:
        return fmt.format(text)


# ============================== reg test ============================== #
"""
计算正则表达式的测试代码
在线版: https://regexr-cn.com/
"""

import re


REG = r"([0-9]+)"
MSG = r"18; 6; 77; 1; 1; 61; 0; 0"

print(" re.compile 方法 ")
"""
完全匹配
"""
pattern = re.compile(REG)
alist = pattern.findall(MSG)
print(alist)

print(" re.match 方法 ")
"""
单次匹配
re.match 尝试从字符串的起始位置匹配一个模式
如果不是起始位置匹配成功的话
match() 就返回 none
"""
pattern = re.match(REG, MSG)
print(pattern.groups())
print(pattern.group(0))


print(" re.search 方法 ")
"""
单次匹配
re.search 扫描整个字符串并返回第一个成功的匹配。
"""
pattern = re.search(REG, MSG)
print(pattern.groups())
print(pattern.group(0))
