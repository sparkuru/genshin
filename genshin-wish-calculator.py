# -*- coding: utf-8 -*-
# 参考 https://github.com/MSIsunny/GenshinWishCalculator-py/blob/main/WishSupport.py

"""
举例

输入：150 3 0 0 1 0 0 0

表示输入条件为：
当前有 150 抽
期望抽到 3 次限定角色(注意从无到 6 命需要 7 次限定金)
角色池已垫 0 抽
当前角色池 不是 大保底
期望抽到 1 个限定定轨武器
武器池已垫 0 抽
当前武器池 不是 大保底
命定值为 0

表示最终想要达成的条件为：
根据输入数据的 150 抽能达到抽到 3 次限定角色和 1 次限定定轨武器

能够 150 抽达成条件概率为：0.33%
267 抽内达成条件的概率为 10%
321 抽内达成条件的概率为 25%
384 抽内达成条件的概率为 50%
450 抽内达成条件的概率为 75%
508 抽内达成条件的概率为 90%
"""

import sys
import argparse
import numpy as np

_IntertwinedFateNum = 120  # 屯屯鼠改这个
DEFAULT = [
    _IntertwinedFateNum,
    3,  # 期望抽到限定角色次数，0-7
    1,  # 当前角色池已垫抽数, 0-89
    1,  # 当前角色池是否为大保底, 0/1
    0,  # 期望抽到限定定轨武器次数, 0-5
    0,  # 当前武器池已垫抽数, 0-79
    0,  # 当前武器池是否为大保底, 0/1
    0,  # 当前武器池的命定值, 0-2
]

ap = argparse.ArgumentParser()
ap.add_argument("--interwined_fate_num", type=int, help="当前拥有的抽数")
ap.add_argument(
    "--expected_character_num",
    type=int,
    help="期望抽到限定角色次数, 0-7, 注意从无到 6 命需要 7 次限定金",
)
ap.add_argument("--character_pool_num", type=int, help="当前角色池已垫抽数, 0-89")
ap.add_argument(
    "--is_character_guarantee", type=int, help="当前角色池是否为大保底, 0/1"
)
ap.add_argument("--expected_weapon_num", type=int, help="期望抽到限定定轨武器次数, 0-5")
ap.add_argument("--weapon_pool_num", type=int, help="当前武器池已垫抽数, 0-79")
ap.add_argument("--is_weapon_guarantee", type=int, help="当前武器池是否为大保底, 0/1")
ap.add_argument("--weapon_pool_binding_num", type=int, help="当前武器池的命定值, 0-2")
ap.add_argument(
    "-d", "--default", default=False, action="store_true", help="使用默认数据生成"
)
ap.add_argument(
    "-g", "--generate", default=False, action="store_true", help="生成 cli 直接调用式"
)
ap.add_argument("-c", "--cmd", default=False, action="store_true", help="cli 调用模式")
ap.add_argument(
    "-i",
    "--interfaces",
    default=False,
    action="store_true",
    help="用户交互方式运行程序",
)

args = vars(ap.parse_args())

interwined_fate_num = args["interwined_fate_num"]
expected_character_num = args["expected_character_num"]
character_pool_num = args["character_pool_num"]
is_character_guarantee = args["is_character_guarantee"]
expected_weapon_num = args["expected_weapon_num"]
weapon_pool_num = args["weapon_pool_num"]
is_weapon_guarantee = args["is_weapon_guarantee"]
weapon_pool_binding_num = args["weapon_pool_binding_num"]

isDefault = args["default"]
isGenerate = args["generate"]
isCmd = args["cmd"]
isInterfaces = args["interfaces"]

banner1 = """
输入条件为：
\033[1;34m|\033[0m 当前有 \033[1;33m{}\033[0m 抽
\033[1;34m|\033[0m 期望抽到 \033[1;33m{}\033[0m 次限定角色
\033[1;34m|\033[0m 角色池已垫 \033[1;33m{}\033[0m 抽
\033[1;34m|\033[0m 当前角色池 \033[1;33m{}\033[0m 大保底
\033[1;34m|\033[0m 期望抽到 \033[1;33m{}\033[0m 个限定定轨武器
\033[1;34m|\033[0m 武器池已垫 \033[1;33m{}\033[0m 抽
\033[1;34m|\033[0m 当前武器池 \033[1;33m{}\033[0m 大保底
\033[1;34m|\033[0m 命定值为 \033[1;33m{}\033[0m
"""

banner2 = """
想要达成的条件为：
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽能抽到 \033[1;33m{}\033[0m 次限定角色和 \033[1;33m{}\033[0m 次限定定轨武器
"""

banner3 = """
能够 \033[1;33m{}\033[0m 抽达成条件概率为：\033[1;33m{}%\033[0m.
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽内达成条件的概率为 \033[1;33m10%\033[0m.
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽内达成条件的概率为 \033[1;33m25%\033[0m.
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽内达成条件的概率为 \033[1;33m50%\033[0m.
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽内达成条件的概率为 \033[1;33m75%\033[0m.
\033[1;34m|\033[0m \033[1;33m{}\033[0m 抽内达成条件的概率为 \033[1;33m90%\033[0m.
"""


def main(
    interwined_fate_num,
    expected_character_num,
    character_pool_num,
    is_character_guarantee,
    expected_weapon_num,
    weapon_pool_num,
    is_weapon_guarantee,
    weapon_pool_binding_num,
):
    if not isValid(
        interwined_fate_num,
        expected_character_num,
        character_pool_num,
        is_character_guarantee,
        expected_weapon_num,
        weapon_pool_num,
        is_weapon_guarantee,
        weapon_pool_binding_num,
    ):
        return

    # 单次抽卡的概率

    # 角色池
    def percent_character(x):
        if x <= 73:
            return 0.006
        elif x <= 89:
            return 0.006 + 0.06 * (x - 73)
        else:
            return 1

    # 武器池
    def percent_weapon(x):
        if x <= 62:
            return 0.007
        elif x <= 73:
            return 0.007 + 0.07 * (x - 62)
        elif x <= 79:
            return 0.777 + 0.035 * (x - 73)
        else:
            return 1

    # 初始化零矩阵
    size = (
        180 * expected_character_num + 400 * expected_weapon_num + 1
    )  # 多加 1 行用于表示达成抽卡预期的状态
    TPmatrix = np.zeros((size, size))

    # 角色池的初始状态设置
    CharacterPoolOffset = 0
    if expected_character_num != 0:
        if is_character_guarantee == False:
            CharacterPoolOffset = character_pool_num
        elif is_character_guarantee == True:
            CharacterPoolOffset = character_pool_num + 90

    # 生成转移概率矩阵（矩阵前面的行是武器，后面的行是角色，最后一行表示的状态是已经达成抽卡预期）
    # 这一部分代码生成抽武器的状态，如果要抽的武器数为0，那么就不会运行这一部分代码
    for i in range(0, expected_weapon_num):
        offset = 400 * i
        for j in range(0, 80):
            x = j % 80 + 1
            if i == expected_weapon_num - 1:
                # 该行属于要抽的最后一把武器的部分，那么如果出限定就会进入角色部分，要加上角色池的初始偏移量
                TPmatrix[offset + j, offset + 400 + CharacterPoolOffset] = (
                    percent_weapon(x) * 0.375
                )
            else:
                # 该行不属于要抽的最后一把武器的部分，那么抽完会进入下一把武器
                TPmatrix[offset + j, offset + 400] = percent_weapon(x) * 0.375
            TPmatrix[offset + j, offset + 160] = percent_weapon(x) * 0.375
            TPmatrix[offset + j, offset + 240] = percent_weapon(x) * 0.25
            TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        for j in range(80, 160):
            x = j % 80 + 1
            if i == expected_weapon_num - 1:
                TPmatrix[offset + j, offset + 400 + CharacterPoolOffset] = (
                    percent_weapon(x) * 0.5
                )
            else:
                TPmatrix[offset + j, offset + 400] = percent_weapon(x) * 0.5
            TPmatrix[offset + j, offset + 160] = percent_weapon(x) * 0.5
            # 在p159状态下抽卡必定成功，故一定会转移到p160状态，这里加上条件判断是为了避免覆盖前面的代码
            if j != 159:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        for j in range(160, 240):
            x = j % 80 + 1
            if i == expected_weapon_num - 1:
                TPmatrix[offset + j, offset + 400 + CharacterPoolOffset] = (
                    percent_weapon(x) * 0.375
                )
            else:
                TPmatrix[offset + j, offset + 400] = percent_weapon(x) * 0.375
            TPmatrix[offset + j, offset + 320] = percent_weapon(x) * 0.625
            TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        for j in range(240, 320):
            x = j % 80 + 1
            if i == expected_weapon_num - 1:
                TPmatrix[offset + j, offset + 400 + CharacterPoolOffset] = (
                    percent_weapon(x) * 0.5
                )
            else:
                TPmatrix[offset + j, offset + 400] = percent_weapon(x) * 0.5
            TPmatrix[offset + j, offset + 320] = percent_weapon(x) * 0.5
            if j != 319:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        for j in range(320, 400):
            x = j % 80 + 1
            if i == expected_weapon_num - 1:
                TPmatrix[offset + j, offset + 400 + CharacterPoolOffset] = (
                    percent_weapon(x)
                )
            else:
                TPmatrix[offset + j, offset + 400] = percent_weapon(x)
            if j != 399:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
    # 这一部分代码生成抽角色的状态，如果要抽的角色数为0，那么就不会运行这一部分代码
    for i in range(0, expected_character_num):
        offset = 180 * i + expected_weapon_num * 400
        for j in range(0, 90):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 180] = percent_character(x) * 0.5
            TPmatrix[offset + j, offset + 90] = percent_character(x) * 0.5
            if j != 89:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        for j in range(90, 180):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 180] = percent_character(x)
            if j != 179:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
    # 最后一行表示已经达成抽卡预期，所以从该状态到其他状态的概率都是0，到自身的概率为1
    TPmatrix[size - 1, size - 1] = 1
    # 生成初始状态向量，如果抽武器，那么和武器池水位有关，否则和角色池水位有关
    initVector = np.zeros((size))
    if expected_weapon_num != 0:
        if weapon_pool_binding_num == 0:
            if is_weapon_guarantee == False:
                initVector[weapon_pool_num] = 1
            elif is_weapon_guarantee == True:
                initVector[weapon_pool_num + 80] = 1
        elif weapon_pool_binding_num == 1:
            if is_weapon_guarantee == False:
                initVector[weapon_pool_num + 160] = 1
            elif is_weapon_guarantee == True:
                initVector[weapon_pool_num + 240] = 1
        elif weapon_pool_binding_num == 2:
            initVector[weapon_pool_num + 320] = 1
    else:  # 这里是不抽武器的情况，和角色池水位有关
        initVector[CharacterPoolOffset] = 1
    # 存储达到10%、25%、50%、75%、90%概率时的抽数
    percent10num = 0
    percent25num = 0
    percent50num = 0
    percent75num = 0
    percent90num = 0
    # 存储达到预期次数的概率
    percentRes = -1
    resultVector = initVector
    for i in range(0, 1500):
        # 将初始状态向量和转移概率矩阵不断相乘，相乘的次数为抽数，得到预期次数后状态的概率分布
        resultVector = resultVector @ TPmatrix
        result = resultVector[size - 1]
        if i == interwined_fate_num - 1:
            percentRes = result
        if result > 0.1 and percent10num == 0:
            percent10num = i + 1
        if result > 0.25 and percent25num == 0:
            percent25num = i + 1
        if result > 0.5 and percent50num == 0:
            percent50num = i + 1
        if result > 0.75 and percent75num == 0:
            percent75num = i + 1
        if result > 0.9 and percent90num == 0:
            percent90num = i + 1
        if percent90num != 0 and percentRes != -1:
            break
    # 输出所有结果
    # print(np.round(percentRes*100,2))
    # print(percent10num)
    # print(percent25num)
    # print(percent50num)
    # print(percent75num)
    # print(percent90num)
    percentRes = str(np.round(percentRes * 100, 2))
    print(
        banner1.format(
            interwined_fate_num,
            expected_character_num,
            character_pool_num,
            "是" if is_character_guarantee else "不是",
            expected_weapon_num,
            weapon_pool_num,
            "是" if is_weapon_guarantee else "不是",
            weapon_pool_binding_num,
        ),
        end="",
    )
    print(
        banner2.format(
            interwined_fate_num, expected_character_num, expected_weapon_num
        ),
        end="",
    )
    print(
        banner3.format(
            interwined_fate_num,
            percentRes,
            percent10num,
            percent25num,
            percent50num,
            percent75num,
            percent90num,
        ),
        end="",
    )
    sys.stdout.flush()


def printCmd(
    interwined_fate_num=interwined_fate_num,
    expected_character_num=expected_character_num,
    character_pool_num=character_pool_num,
    is_character_guarantee=is_character_guarantee,
    expected_weapon_num=expected_weapon_num,
    weapon_pool_num=weapon_pool_num,
    is_weapon_guarantee=is_weapon_guarantee,
    weapon_pool_binding_num=weapon_pool_binding_num,
):
    print(
        "python \033[1;33m{}\033[0m -c --interwined_fate_num=\033[1;33m{}\033[0m --expected_character_num=\033[1;33m{}\033[0m --character_pool_num=\033[1;33m{}\033[0m --is_character_guarantee=\033[1;33m{}\033[0m --expected_weapon_num=\033[1;33m{}\033[0m --weapon_pool_num=\033[1;33m{}\033[0m --is_weapon_guarantee=\033[1;33m{}\033[0m --weapon_pool_binding_num=\033[1;33m{}\033[0m".format(
            __file__,
            interwined_fate_num,
            expected_character_num,
            character_pool_num,
            is_character_guarantee,
            expected_weapon_num,
            weapon_pool_num,
            is_weapon_guarantee,
            weapon_pool_binding_num,
        )
    )


def interfaces():
    pass


def isValid(
    interwined_fate_num,
    expected_character_num,
    character_pool_num,
    is_character_guarantee,
    expected_weapon_num,
    weapon_pool_num,
    is_weapon_guarantee,
    weapon_pool_binding_num,
) -> bool:
    (
        interwined_fate_num,
        expected_character_num,
        character_pool_num,
        is_character_guarantee,
        expected_weapon_num,
        weapon_pool_num,
        is_weapon_guarantee,
        weapon_pool_binding_num,
    )
    if interwined_fate_num < 0 and interwined_fate_num > 1500:
        print("目前持有的 纠缠之缘数量 应该大于等于 0 (原石请自行换算).")
        return False
    if expected_character_num < 0 and expected_character_num > 7:
        print("目标获得的 限定角色卡数量 应该处于 0 ~ 7 之间.")
        return False
    if character_pool_num < 0 and character_pool_num > 89:
        print("已垫限定角色卡池抽数 应该处于 0 ~ 89 之间.")
        return False
    if is_character_guarantee not in [0, 1]:
        print("限定角色卡池是否为大保底的状态 只有 0 或 1.")
        return False
    if expected_weapon_num < 0 and expected_weapon_num > 5:
        print("目标获得的 限定且目标定轨武器数量 应该处于 0 ~ 5 之间.")
        return False
    if weapon_pool_num < 0 and weapon_pool_num > 79:
        print("已垫限定且目标定轨武器卡池抽数 应该处于 0 ~ 79 之间.")
        return False
    if is_weapon_guarantee not in [0, 1]:
        print("限定且定轨的武器卡池是否为保底的状态 只有 0 或 1.")
        return False
    if weapon_pool_binding_num not in [0, 1, 2]:
        print("武器卡池的定轨状态 只有 0, 1, 2.")
        return False
    return True


def fgx(type=1, text="分割线", length="30", isPrint=True):
    # print("{:=^60s}".format('分割线'))
    fmt = "\033[1;34m{:type^lengths}\033[0m".replace("length", length)

    SWITCH = {
        1: "-",
        2: "=",
        3: "✩",
    }

    if type not in SWITCH.keys():
        type = 1
    fmt = fmt.replace("type", SWITCH.get(type))

    if isPrint:
        print(fmt.format(text))
        return None
    else:
        return fmt.format(text)


if isDefault:
    fgx(text="选择使用默认数据集")
    main(
        DEFAULT[0],
        DEFAULT[1],
        DEFAULT[2],
        DEFAULT[3],
        DEFAULT[4],
        DEFAULT[5],
        DEFAULT[6],
        DEFAULT[7],
    )
elif isGenerate:
    fgx(text="选择生成 cmd 调用式")
    printCmd(
        DEFAULT[0],
        DEFAULT[1],
        DEFAULT[2],
        DEFAULT[3],
        DEFAULT[4],
        DEFAULT[5],
        DEFAULT[6],
        DEFAULT[7],
    )
elif isCmd:
    fgx(text="选择 cmd 直接调用模式")
    main(
        interwined_fate_num,
        expected_character_num,
        character_pool_num,
        is_character_guarantee,
        expected_weapon_num,
        weapon_pool_num,
        is_weapon_guarantee,
        weapon_pool_binding_num,
    )
elif isInterfaces:
    fgx(text="选择用户交互模式")
    interfaces()
else:
    fgx(text="输入指令以调用程序, 使用 -h 以获取更多帮助")
