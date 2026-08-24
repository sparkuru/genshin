个人定制化的 rime：fcitx5 + rime + [rime_mint](https://www.mintimate.cc/)

## usage

用户配置目录在 `~/.local/share/fcitx5/rime/`

安装 fcitx5 和 rime

```bash
to_install=(
    fcitx5
    fcitx5-anthy
    fcitx5-chinese-addons
    fcitx5-chinese-addons-bin
    fcitx5-chinese-addons-data
    fcitx5-config-qt
    fcitx5-data
    fcitx5-frontend-all
    fcitx5-frontend-gtk2
    fcitx5-frontend-gtk3
    fcitx5-frontend-gtk4
    fcitx5-frontend-qt5
    fcitx5-frontend-qt6
    fcitx5-module-chttrans
    fcitx5-module-cloudpinyin
    fcitx5-module-fullwidth
    fcitx5-module-lua
    fcitx5-module-lua-common
    fcitx5-module-pinyinhelper
    fcitx5-module-punctuation
    fcitx5-modules
    fcitx5-pinyin
    fcitx5-pinyin-gui
    fcitx5-rime
    fcitx5-table
    kde-config-fcitx5
    libfcitx5-qt-data
    libfcitx5-qt1
    libfcitx5-qt6-1
    libfcitx5config6
    libfcitx5core7
    libfcitx5gclient2
    libfcitx5utils2
    libcolorhug2
    librime-bin
    librime-data
    librime-plugin-charcode
    librime-plugin-lua
    librime-plugin-octagram
    librime1t64
    python3-typing-extensions
    rime-data-bopomofo
    rime-data-cangjie5
    rime-data-emoji
    rime-data-luna-pinyin
    rime-data-stroke
    rime-data-terra-pinyin
    rime-essay
    rime-prelude
)

sudo apt update
sudo apt install -y ${to_install[@]}
```

rime 用户配置目录在 `~/.local/share/fcitx5/rime/`，获取 rime_mint

```bash
$ mkdir -p ~/.local/share/fcitx5/rime && cd ~/.local/share/fcitx5/rime
$ git clone https://github.com/Mintimate/oh-my-rime.git ~/.local/share/fcitx5/rime

$ curl -fl -o ~/.local/share/fcitx5/rime/rime_mint.custom.yaml https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/tsuki/24-rime/custom/rime_mint.custom.yaml
```

部署：

1.   构建：`rime_deployer --build ~/.local/share/fcitx5/rime /usr/share/rime-data ~/.local/share/fcitx5/rime/build`
2.   重载 fcitx5：`fcitx5-remote -r`

建议的修改原则如下：

1.   不直接改 `*.schema.yaml` / `default.yaml`，升级时会被覆盖
2.   一律通过 `*.custom.yaml` 写 patch，字段路径用 `/` 分隔
3.   patch 文件命名：
     - 全局：`default.custom.yaml`
     - 单方案：`<schema_id>.custom.yaml`（如 `rime_mint.custom.yaml`）
4.   fcitx5 配置工具里的 addon 选项只覆盖 addon 自身（共享数据路径、模块开关、输入法切换键），不涉及任何 RIME 内部行为（候选数、模糊音、词库、键绑定、开关项），所有 RIME 内部定制必须 YAML + 重新部署

## 可迁移备份

`custom/` 保存的是 Rime 用户层覆盖，不是完整的 `~/.local/share/fcitx5/rime` 镜像。当前特别配置包括：

- `custom/default.yaml`：保留当前禁用 `Shift+Space` 全角切换的版本
- `custom/rime_mint.custom.yaml`：候选页、拼音容错和 `bun` 候选过滤器
- `custom/dicts/custom_simple.dict.yaml`：个人词条，包括 `bun\t不能`
- `custom/lua/remove_bun_candidate.lua`：只在输入 `bun` 时移除 `兺`
- `custom/user.yaml`：当前选中的 `rime_mint` 方案
- `custom/state/*.userdb.txt`：可选的用户词频文本，可能包含个人输入内容

`backup.sh` 会从本机 Rime 目录读取这些运行配置；`restore.sh` 会在本机 Rime 目录中为运行配置创建指向 `custom/` 的符号链接，其中 `custom/lua/*.lua` 会逐个链接到本机 `lua/` 的同名路径。`manifest.yaml` 和 `state/*.userdb.txt` 只用于备份与恢复，不会链接到 Rime 目录。

不备份 `build/`、`installation.yaml` 和二进制 `*.userdb`。这些内容分别是可重建产物、设备标识和正在运行的 LevelDB 状态。

### 刷新当前设备的备份

```bash
cd /home/wkyuu/cargo/repo/04-flyMe2theStar/03-genshin/tsuki/24-rime
./backup.sh --force --with-userdb
```

`--with-userdb` 会保存最近一次 Rime 同步导出的用户词频。若需导出最新实时词频，应先退出或停止 Fcitx5，再在 Rime 用户目录执行：

```bash
cd /home/wkyuu/.local/share/fcitx5/rime
rime_dict_manager --backup rime_mint
rime_dict_manager --backup melt_eng
```

随后再次运行 `./backup.sh`。

### 新设备恢复

先安装 `fcitx5-rime`、`librime-bin`、`librime-plugin-lua`、`librime-plugin-octagram`、`librime1t64` 和 `librime-data`，再准备同一版本的 [oh-my-rime](https://github.com/Mintimate/oh-my-rime) 基础目录。`custom/manifest.yaml` 记录了当前基础仓库提交和 Rime 版本。

确认 Fcitx5 Rime 已初始化后执行：

```bash
cd /home/wkyuu/cargo/repo/04-flyMe2theStar/03-genshin/tsuki/24-rime
./restore.sh --force --with-userdb
```

如果只恢复配置而不恢复词频，去掉 `--with-userdb`。恢复脚本会建立配置链接并重新部署 Rime；若当前终端没有 D-Bus，需从桌面会话重启 Fcitx5。换设备或更换仓库路径后，仍需运行一次 `./restore.sh`，由脚本按当前位置重建绝对路径链接。

常用 patch 路径速查

| 路径 | 作用 |
|---|---|
| `menu/page_size` | 每页候选数（默认 6） |
| `menu/alternative_select_keys` | 选词键（默认 `"1234567890"`） |
| `speller/algebra` | 拼写匹配规则：模糊音 / 简拼 / 容错 |
| `speller/auto_select` | 唯一候选自动上屏 |
| `speller/delimiter` | 拼音分隔符（默认 `" '"`） |
| `key_binder/bindings` | 快捷键绑定 |
| `punctuator/half_shape` `punctuator/full_shape` | 半/全角标点表 |
| `translator/enable_user_dict` | 是否记忆词频 |
| `translator/enable_word_completion` | 长词自动补全 |
| `switches` | 中英 / 繁简 / 标点等开关项 |

speller/algebra 规则类型

| 类型 | 作用 | 示例 |
|---|---|---|
| `xlit/A/B/` | 字符逐位替换（A、B 等长字符串） | `xlit/üÜ/vV/` |
| `xform/regex/repl/` | 正则替换（替换原拼写） | `xform/([jqxy])v/$1u/` |
| `derive/regex/repl/` | 正则派生（追加别名，原拼写保留） | `derive/([jqxy])u/$1v/` |
| `abbrev/regex/repl/` | 缩写派生（追加，用于首字母简拼） | `abbrev/^([a-z]).+$/$1/` |
| `erase/regex/` | 删除匹配的拼写 | `erase/^xx$/` |

薄荷拼音内置的容错规则

| 规则 | 例子 |
|---|---|
| `derive/([aeiou])ng$/$1gn/` | `dagn → dang` |
| `derive/([zcs])h(...)/h$1$2/` | `hzi → zhi` |
| `derive/^([zcs]h).+$/$1/` | `zho → zhong / zhou` |
| `derive/^([wghk])ai$/$1ia/` | `wia → wai` |
| ... | 打错位置仍能出字 |

## refer

1.   薄荷拼音：https://github.com/Mintimate/oh-my-rime
2.   雾凇拼音：https://github.com/iDvel/rime-ice
3.   RIME 配置文档：https://github.com/rime/home/wiki/CustomizationGuide
4.   algebra 规则：https://github.com/rime/home/wiki/RimeWithSchemata
