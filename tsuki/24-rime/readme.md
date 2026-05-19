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

$ curl -fl -o ~/.local/share/fcitx5/rime/rime_mint.custom.yaml https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/tsuki/24-rime/rime_mint.custom.yaml
```

部署：

1.   构建：`rime_deployer --build ~/.local/share/fcitx5/rime`；如果构建修改无效，就强制构建：`rm -f build/rime_mint.*.bin build/rime_mint.schema.yaml`
2.   重载 fcitx5：`fcitx5-remote -r`

建议的修改原则如下：

1.   不直接改 `*.schema.yaml` / `default.yaml`，升级时会被覆盖
2.   一律通过 `*.custom.yaml` 写 patch，字段路径用 `/` 分隔
3.   patch 文件命名：
     - 全局：`default.custom.yaml`
     - 单方案：`<schema_id>.custom.yaml`（如 `rime_mint.custom.yaml`）
4.   fcitx5 配置工具里的 addon 选项只覆盖 addon 自身（共享数据路径、模块开关、输入法切换键），不涉及任何 RIME 内部行为（候选数、模糊音、词库、键绑定、开关项），所有 RIME 内部定制必须 YAML + 重新部署

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
