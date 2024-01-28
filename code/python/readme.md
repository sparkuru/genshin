## python-embed-env-maker

### windows

windows 下通过 python embedable package 快速创建不同版本的可移植环境（venv），以 python 3.12 为例

1. 在项目下创建文件夹 `.venv`
2. 到 [官网](https://www.python.org/downloads/release/python-3120/) 下载对应的 embedable package，解压到 `.venv/` 下
3. 补全 python 能力：pip、virtualenv
   1. 获取 pip：`wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py`
   2. 在 `.venv/python-3.12.0-embed-amd64/python12._pth` 中去掉 `# import site` 前的注释号
   3. 安装 pip：`.venv/python-3.12.0-embed-amd64/python.exe get-pip.py`
   4. `.venv/python-3.12.0-embed-amd64/python.exe -m pip install virtualenv`
4. 然后创建虚拟环境：`.venv/python-3.12.0-embed-amd64/python.exe -m virtualenv .venv`（选定 `.venv` 目录作为虚拟环境，且移植后也可以直接使用）
5. `./.venv/scripts/activate`

### unix

由于官网上并没有提供 unix 的 portable 程序，需要自己手动编译：

1. 在项目下创建文件夹 `.venv`，安装必要编译工具：`sudo apt install build-essential autoconf automake`
2. 到 [官网](https://www.python.org/downloads/release/python-3131/) 下载源码 `Gzipped source tarball`，解压到 `.venv/` 下：`tar zxvf Python-3.13.1.tgz`
3. 编译
   1. `cd Python-3.13.1`，`mkdir portable-output`
   2. `./configure --prefix=$PWD/portable-output --with-ensurepip=install`，在这里可以预先指定安装 pip
   3. `make` 开始编译
   4. `make install` 编译完成后安装到上述提供的 `portable-output`
   5. 此时将 `portable-output` 目录整个打包即为 python 的 porable 环境：`mv portable-output ../python`
4. 安装虚拟环境
   1. `.venv/python/bin/python3 -m pip install virtualenv`
   2. `.venv/python/bin/python3 -m pip virtualenv .venv`
5. `source .venv/bin/activate`

以上步骤完成后，python 项目的目录结构应该如下（unix 相似）：

```bash
project
├── .venv
│   ├── python-3.12.0-embed-amd64
│   │   ├── python.exe
│   │   ├── pythonw.exe
│   │   ├── python312.zip
│   │   └── ...
│   ├── Lib
│   │   └── site-packages
│   ├── Scripts
│   │   ├── activate
│   │   ├── activate.bat
│   │   ├── activate.ps1
│   │   ├── pip.exe
│   │   ├── python.exe
│   │   └── ...
│   ├── python-3.12.0-embed-amd64.zip
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   └── pyvenv.cfg
├── src
│   ├── entry.py
│   ├── util.py
│   └── ...
├── README.md
└── main.py
```

## sugar

### 装饰器 decorator

如果想知道 `print_prime` 总共花费的时间

```python
def is_prime(n):
    if n <= 1: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def print_prime(max_num):
    import time
    t1 = time.time()
    count = 0
    for num in range(2, max_num + 1):
        if is_prime(num):
            count += 1
            print(num)
  t2 = time.time()
    print('time spend: {}; total: {}'.format(t2 - t1, count))

def print_prime2(max_num):
    import time
    t1 = time.time()
    count = 0
    for num in range(2, max_num + 1 + 10000):
        if is_prime(num):
            count += 1
            print(num)
  t2 = time.time()
    print('time spend: {}; total: {}'.format(t2 - t1, count))

max_num = 10000
print_prime(max_num)
```

使用装饰器后转为以下内容

```python
def print_prime_decorator(func):
  def wrapper(*args):
      import time
      t1 = time.time()
      result = func(*args)
      t2 = time.time()
      print('time spend: {}'.format(t2 - t1))
      return result
  return wrapper

def is_prime(n):
  if n <= 1: return False
  for i in range(2, int(n**0.5) + 1):
      if n % i == 0: return False
  return True

@print_prime_decorator
def print_prime(max_num):
  for num in range(2, max_num + 1):
      if is_prime(num):
          print(num)

@print_prime_decorator
def print_prime2(max_num):
    for num in range(2, max_num + 1 + 10000):
        if is_prime(num):
            print(num)

max_num = 10000
print_prime(max_num)
print_prime2(max_num)
```

函数执行时，会先进入到 wrapper 中，情况适用于需要大量重复相同的代码，如此一来只需要在函数前添加一个装饰器函数即可，提升代码可读性

### 类 class

tab

## script

缺什么 package 补什么

### password-generator.py

1. 增强版 `--salt`：用 seed 生成一个针对于特定机器码的伪 salt 文件，即使用 `--seed` 和 `--salt` 多因素来创建 password
2. 后续如果要得出相同的 password 需要再指定该 salt 文件，丢了就是丢了

### ez-encrypt.py

1. `python ./03-ez-encrypt.py -h` 查看帮助
2. 默认使用 prompt 输入 key，也可以手动指定：`-k path/to/keyfile`
3. `salt` 盐文件和输入的 key 与 uuid 有关，指定 `-s` 选项后需要提供一个盐路径，如果不存在会自动生成
4. 指定 `-d` 会在加密后提示是否删除源文件
5. 示例
    1.   **注意，操作之前，如果不主动指定 output，会自动覆盖掉解密后的同名文件，如果密码错了该文件会丢失**
    2.   对单个文件进行加密：`python ./02-ez-encrypt.py -i plain/03-ez-encrypt.md -s salt enc`
    3.   对单个文件进行解密：`python ./02-ez-encrypt.py -i plain/03-ez-encrypt.md.enc dec`
    4.   对目录下文件进行加密，并递归处理：`python ./03-ez-encrypt.py -i path/to/enc_dir -r -s salt enc`
    5.   对目录下文件进行解密，并递归处理：`python ./03-ez-encrypt.py -i path/to/enc_dir -r dec`

### ls-alh

模拟 `ls -alh`，`alias alh="python ls_alh.py"`

### lcd

存储 cd list，`alias lcd="python cd.py"`，可以直接复制使用

1.   `lcd -h`

2.   `lcd -a .`，添加一个路径记录

3.   `lcd -l`，列出所有路径记录；`lcd -l -n 3`，列出第 3 条记录，主要是配合以下 bash function

     ```bash
     lcd() {
         lcd_path="$HOME/.genshin/lcd.py"
         if [[ ! -f $lcd_path ]]; then
             _curl $lcd_path $github_url_base/script/04-cmd-implementation/02-lcd.py
         fi
         if [[ "$1" == "cd" && ! -z "$2" ]]; then
             target_dir=$(python $lcd_path -pn "$2")
             cd "$target_dir"
         elif [[ "$1" == "l" ]]; then
             python3 $lcd_path -l
         elif [[ "$1" == "d" && ! -z "$2" ]]; then
             python3 $lcd_path -d -n "$2"
         elif [[ "$1" == "a" && ! -z "$2" ]]; then
             python3 $lcd_path -a "$2"
         else
             python3 $lcd_path "$@"
         fi
     }
     ```

     `lcd l`、`lcd cd 2`、`lcd d 2`、`lcd $args`

4.   `lcd -d /tmp/tmp`，删除路径记录；`lcd -d /tmp/tmp -n 3`，删除第三条记录，此时指定的 `/tmp/tmp` 无效

### interact-rename.py

```bash
PS C:\Users\wkyuu\Desktop\mods> rename -h
usage: interact_rename.py [-h] [-w WIDTH] [-t TYPE] [-m MODE] [--start_num START_NUM] [-x EXCLUDE [EXCLUDE ...]]
                          [-o OLD] [-n NEW] [-d]
                          foobar

用于在当前文件夹下进行批量重命名; e.g.: rename foobar -x x1.txt x2.ini | rename -w 3 -t img fast | rename
-w 3 -m add prefix | rename interact | rename -o '-' -n '_' replace | rename show
| rename -w 3 sort | rename test

positional arguments:
  foobar                fast 执行快速重命名 | prefix 执行前缀操作式重命名 | interact 执行交互式重命名 |
                        replace 快速修改文件名中的指定字符 | show 列出程序预处理文件队列 | sort
                        预览添加前缀并排序的文件队列 | test 生成测试文件

optional arguments:
  -h, --help            show this help message and exit
  -w WIDTH, --width WIDTH
                        指定重命名前缀或快速重命名时, index 格式长度, 默认 3
  -t TYPE, --type TYPE  指定快速重命名时要处理的类型, 默认 img, 可选 img 或 video
  -m MODE, --mode MODE  指定快速添加前缀重命名时的模式, 默认 add, 可选 add 或 remove
  --start_num START_NUM
                        指定快速添加前缀重命名时的起始数字, 默认 1
  -x EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                        指定要排除的文件名, 如果有多个需要多次指定, 且必须写在 foobar 后面
  -o OLD, --old OLD     要替换的旧字符
  -n NEW, --new NEW     要替换成的新字符
  -d, --directory       是否处理文件夹, 添加即处理
```

1.   `alias rename = "python interact_rename.py"`
2.   `rename foobar -x x1.txt x2.ini`，排除文件（除了指定要排除的文件，还内置一套常见不该操作的文件名）
3.   `rename -w 3 -t img fast`，对当前目录下所有 img 类型的文件执行快速重命名，prefix 从 001 开始
4.   `rename -w 3 -m add --start_num 5 prefix`，对当前目录下所有可识别的文件进行 **添加** 指定 width 长度的前缀的重命名，并且指定开始的数字为 005
5.   `rename -w 3 -m remove prefix`，对当前目录下所有可识别的文件进行 **去掉** 指定 width 长度的前缀的重命名
6.   `rename interact`，交互式重命名
7.   `rename -o '-' -n '_' replace`，将全部文件名中的 `-` 改成 `_`
8.   `rename show`，预览所有被添加到处理队列的文件名
9.   `rename -w 3 sort`，快速地对当前目录下所有可识别的文件进行排序并添加 width 为 3 的前缀
10.   `rename test`，测试用，使用 `touch` 生成一些可能的文件名

使用范式

1. `rename -w 3 -m add prefix`，为当前目录下所有文件添加一个 *xxx_* 数字前缀，默认从 1 开始，还可以指定 `--num 5` 从 5 开始

   ```powershell
   PS C:\Users\wkyuu\Desktop\mods> rename -w 3 -m add prefix
   | 【a-prefix】：ApothicAttributes-1.20.1-1.3.1.jar => 001_【a-prefix】：ApothicAttributes-1.20.1-1.3.1.jar
   | 【a-prefix】：Bookshelf-Forge-1.20.1-20.1.10.jar => 002_【a-prefix】：Bookshelf-Forge-1.20.1-20.1.10.jar
   | 【a-prefix】：BotanyPots-Forge-1.20.1-13.0.29.jar => 003_【a-prefix】：BotanyPots-Forge-1.20.1-13.0.29.jar
   | 【a-prefix】：CerbonsAPI-Forge-1.20.1-1.1.0.jar => 004_【a-prefix】：CerbonsAPI-Forge-1.20.1-1.1.0.jar
   | 【a-prefix】：CorgiLib-forge-1.20.1-4.0.1.1.jar => 005_【a-prefix】：CorgiLib-forge-1.20.1-4.0.1.1.jar
   | 【a-prefix】：CreativeCore_FORGE_v2.11.24_mc1.20.1.jar => 006_【a-prefix】：CreativeCore_FORGE_v2.11.24_mc1.20.1.jar
   | 【a-prefix】：EdivadLib-1.20.1-2.0.1.jar => 007_【a-prefix】：EdivadLib-1.20.1-2.0.1.jar
   | 【a-prefix】：LibX-1.20.1-5.0.12.jar => 008_【a-prefix】：LibX-1.20.1-5.0.12.jar
   | 【a-prefix】：Patchouli-1.20.1-84-FORGE.jar => 009_【a-prefix】：Patchouli-1.20.1-84-FORGE.jar
   | 【a-prefix】：Placebo-1.20.1-8.6.1.jar => 010_【a-prefix】：Placebo-1.20.1-8.6.1.jar
   | ...
   ```

   1.   `-w 3`，width，表示 xxx 的宽度，2 就是 xx

   2.   `-m`，mode，表示模式；如果改成 `-m remove`，就是自动识别上面的数字前缀并删除

        ```powershell
        PS C:\Users\wkyuu\Desktop\mods> rename -w 3 -m remove prefix
        | 001_【a-prefix】：ApothicAttributes-1.20.1-1.3.1.jar => 【a-prefix】：ApothicAttributes-1.20.1-1.3.1.jar
        | 002_【a-prefix】：Bookshelf-Forge-1.20.1-20.1.10.jar => 【a-prefix】：Bookshelf-Forge-1.20.1-20.1.10.jar
        | 003_【a-prefix】：BotanyPots-Forge-1.20.1-13.0.29.jar => 【a-prefix】：BotanyPots-Forge-1.20.1-13.0.29.jar
        | 004_【a-prefix】：CerbonsAPI-Forge-1.20.1-1.1.0.jar => 【a-prefix】：CerbonsAPI-Forge-1.20.1-1.1.0.jar
        | 005_【a-prefix】：CorgiLib-forge-1.20.1-4.0.1.1.jar => 【a-prefix】：CorgiLib-forge-1.20.1-4.0.1.1.jar
        | 006_【a-prefix】：CreativeCore_FORGE_v2.11.24_mc1.20.1.jar => 【a-prefix】：CreativeCore_FORGE_v2.11.24_mc1.20.1.jar
        | 007_【a-prefix】：EdivadLib-1.20.1-2.0.1.jar => 【a-prefix】：EdivadLib-1.20.1-2.0.1.jar
        | ...
        ```

2.   `rename -o '-' -n '_' replace`，将当前目录下所有文件名中的 `-` 修改成 `_`，`-o` 就是 old，`-n` 就是 new

3.   `rename foobar -x 'file1' 'file2'` 指定 `-x` 可以排除哪些不想处理的文件名

4.   `rename -d foobar`，默认不处理文件夹名字，指定 `-d` 可以处理文件夹

比如从 pcl 下载了以下文件

```powershell
resourcefullib-forge-1.20.1-2.1.24.jar
[3D皮肤层] skinlayers3d-forge-1.6.2-mc1.20.1.jar
[alex的生物请务必把复刻怪的生成凋成0避免影响平衡] alexsmobs-1.22.8.jar
```

假设 `resourcefullib` 是 `alexsmobs` 的前置，`skinlayers3d` 是不影响玩法的增强型辅助 mod，`alexsmobs` 是影响玩法的 mod，则可以为他们修改成以下文件名

```powershell
[a-prefix] resourcefullib-forge-1.20.1-2.1.24.jar
[b-extention-3D皮肤层] skinlayers3d-forge-1.6.2-mc1.20.1.jar
[c-mod-alex的生物请务必把复刻怪的生成凋成0避免影响平衡] alexsmobs-1.22.8.jar
```

其中的 a、b、c 只是为了在后续使用快速命名时，能先被处理（即处理后数字更前，跟排序时看第一个字符一个意思），得到以下目录

```powershell
PS C:\Users\wkyuu\Desktop\mods> fd
[a-prefix] ApothicAttributes-1.20.1-1.3.1.jar
[a-prefix] Searchables-forge-1.20.1-1.0.2.jar
[a-prefix] architectury-9.2.14-forge.jar
[a-prefix] resourcefulconfig-forge-1.20.1-2.1.2.jar
[a-prefix] resourcefullib-forge-1.20.1-2.1.24.jar
[a-prefix] supermartijn642configlib-1.1.8a-fabric-mc1.20.jar
[b-extention-3D皮肤层] skinlayers3d-forge-1.6.2-mc1.20.1.jar
[b-extention-fps优化] betterfpsdist-1.20.1-4.3.jar
[b-extention-自动汉化更新] I18nUpdateMod-3.5.3-all.jar
[b-extention-自动爬坡] stepitup-2.0.1-1.20.1-forge.jar
[c-mod-alex的生物请务必把复刻怪的生成凋成0避免影响平衡] alexsmobs-1.22.8.jar
[c-mod-紫晶钻-diamethysts] diamethysts-1.9.2-1.20.1.jar
[c-mod-自动钓鱼Forge版] forgeautofish-6.0.0-1.20.1.jar
[c-mod-自然群系指南针] NaturesCompass-1.20.1-1.11.2-forge.jar
```

为了避免歧义，想要去掉其中的空格

```powershell
PS C:\Users\wkyuu\Desktop\mods> rename -o '] ' -n ']' replace
| [a-prefix] ApothicAttributes-1.20.1-1.3.1.jar => [a-prefix]ApothicAttributes-1.20.1-1.3.1.jar
| [a-prefix] Searchables-forge-1.20.1-1.0.2.jar => [a-prefix]Searchables-forge-1.20.1-1.0.2.jar
| [a-prefix] architectury-9.2.14-forge.jar => [a-prefix]architectury-9.2.14-forge.jar
| [a-prefix] resourcefulconfig-forge-1.20.1-2.1.2.jar => [a-prefix]resourcefulconfig-forge-1.20.1-2.1.2.jar
| [a-prefix] resourcefullib-forge-1.20.1-2.1.24.jar => [a-prefix]resourcefullib-forge-1.20.1-2.1.24.jar
| [a-prefix] supermartijn642configlib-1.1.8a-fabric-mc1.20.jar => [a-prefix]supermartijn642configlib-1.1.8a-fabric-mc1.20.jar
| [b-extention-3D皮肤层] skinlayers3d-forge-1.6.2-mc1.20.1.jar => [b-extention-3D皮肤层]skinlayers3d-forge-1.6.2-mc1.20.1.jar
| [b-extention-fps优化] betterfpsdist-1.20.1-4.3.jar => [b-extention-fps优化]betterfpsdist-1.20.1-4.3.jar
| [b-extention-自动汉化更新] I18nUpdateMod-3.5.3-all.jar => [b-extention-自动汉化更新]I18nUpdateMod-3.5.3-all.jar
| [b-extention-自动爬坡] stepitup-2.0.1-1.20.1-forge.jar => [b-extention-自动爬坡]stepitup-2.0.1-1.20.1-forge.jar
| [c-mod-alex的生物请务必把复刻怪的生成凋成0避免影响平衡] alexsmobs-1.22.8.jar => [c-mod-alex的生物请务必把复刻怪的生成 凋成0避免影响平衡]alexsmobs-1.22.8.jar
| [c-mod-紫晶钻-diamethysts] diamethysts-1.9.2-1.20.1.jar => [c-mod-紫晶钻-diamethysts]diamethysts-1.9.2-1.20.1.jar
| [c-mod-自动钓鱼Forge版] forgeautofish-6.0.0-1.20.1.jar => [c-mod-自动钓鱼Forge版]forgeautofish-6.0.0-1.20.1.jar
| [c-mod-自然群系指南针] NaturesCompass-1.20.1-1.11.2-forge.jar => [c-mod-自然群系指南针]NaturesCompass-1.20.1-1.11.2-forge.jar
```

最后排序

```powershell
PS C:\Users\wkyuu\Desktop\mods> rename -w 2 -m add prefix
| [a-prefix]ApothicAttributes-1.20.1-1.3.1.jar => 01_[a-prefix]ApothicAttributes-1.20.1-1.3.1.jar
| [a-prefix]Searchables-forge-1.20.1-1.0.2.jar => 02_[a-prefix]Searchables-forge-1.20.1-1.0.2.jar
| [a-prefix]architectury-9.2.14-forge.jar => 03_[a-prefix]architectury-9.2.14-forge.jar
| [a-prefix]resourcefulconfig-forge-1.20.1-2.1.2.jar => 04_[a-prefix]resourcefulconfig-forge-1.20.1-2.1.2.jar
| [a-prefix]resourcefullib-forge-1.20.1-2.1.24.jar => 05_[a-prefix]resourcefullib-forge-1.20.1-2.1.24.jar
| [a-prefix]supermartijn642configlib-1.1.8a-fabric-mc1.20.jar => 06_[a-prefix]supermartijn642configlib-1.1.8a-fabric-mc1.20.jar
| [b-extention-3D皮肤层]skinlayers3d-forge-1.6.2-mc1.20.1.jar => 07_[b-extention-3D皮肤层]skinlayers3d-forge-1.6.2-mc1.20.1.jar
| [b-extention-fps优化]betterfpsdist-1.20.1-4.3.jar => 08_[b-extention-fps优化]betterfpsdist-1.20.1-4.3.jar
| [b-extention-自动汉化更新]I18nUpdateMod-3.5.3-all.jar => 09_[b-extention-自动汉化更新]I18nUpdateMod-3.5.3-all.jar
| [b-extention-自动爬坡]stepitup-2.0.1-1.20.1-forge.jar => 10_[b-extention-自动爬坡]stepitup-2.0.1-1.20.1-forge.jar
| [c-mod-alex的生物请务必把复刻怪的生成凋成0避免影响平衡]alexsmobs-1.22.8.jar => 11_[c-mod-alex的生物请务必把复刻怪的生 成凋成0避免影响平衡]alexsmobs-1.22.8.jar
| [c-mod-紫晶钻-diamethysts]diamethysts-1.9.2-1.20.1.jar => 12_[c-mod-紫晶钻-diamethysts]diamethysts-1.9.2-1.20.1.jar
| [c-mod-自动钓鱼Forge版]forgeautofish-6.0.0-1.20.1.jar => 13_[c-mod-自动钓鱼Forge版]forgeautofish-6.0.0-1.20.1.jar
| [c-mod-自然群系指南针]NaturesCompass-1.20.1-1.11.2-forge.jar => 14_[c-mod-自然群系指南针]NaturesCompass-1.20.1-1.11.2-forge.jar
```

（可选）如果新增 mod 想要重新排序，先去掉排序

```powershell
PS C:\Users\wkyuu\Desktop\mods> rename -w 2 -m remove prefix
| 01_[a-prefix]ApothicAttributes-1.20.1-1.3.1.jar => [a-prefix]ApothicAttributes-1.20.1-1.3.1.jar
| 02_[a-prefix]Searchables-forge-1.20.1-1.0.2.jar => [a-prefix]Searchables-forge-1.20.1-1.0.2.jar
| 03_[a-prefix]architectury-9.2.14-forge.jar => [a-prefix]architectury-9.2.14-forge.jar
| 04_[a-prefix]resourcefulconfig-forge-1.20.1-2.1.2.jar => [a-prefix]resourcefulconfig-forge-1.20.1-2.1.2.jar
| 05_[a-prefix]resourcefullib-forge-1.20.1-2.1.24.jar => [a-prefix]resourcefullib-forge-1.20.1-2.1.24.jar
| 06_[a-prefix]supermartijn642configlib-1.1.8a-fabric-mc1.20.jar => [a-prefix]supermartijn642configlib-1.1.8a-fabric-mc1.20.jar
| 07_[b-extention-3D皮肤层]skinlayers3d-forge-1.6.2-mc1.20.1.jar => [b-extention-3D皮肤层]skinlayers3d-forge-1.6.2-mc1.20.1.jar
| 08_[b-extention-fps优化]betterfpsdist-1.20.1-4.3.jar => [b-extention-fps优化]betterfpsdist-1.20.1-4.3.jar
| 09_[b-extention-自动汉化更新]I18nUpdateMod-3.5.3-all.jar => [b-extention-自动汉化更新]I18nUpdateMod-3.5.3-all.jar
| 10_[b-extention-自动爬坡]stepitup-2.0.1-1.20.1-forge.jar => [b-extention-自动爬坡]stepitup-2.0.1-1.20.1-forge.jar
| 11_[c-mod-alex的生物请务必把复刻怪的生成凋成0避免影响平衡]alexsmobs-1.22.8.jar => [c-mod-alex的生物请务必把复刻怪的生 成凋成0避免影响平衡]alexsmobs-1.22.8.jar
| 12_[c-mod-紫晶钻-diamethysts]diamethysts-1.9.2-1.20.1.jar => [c-mod-紫晶钻-diamethysts]diamethysts-1.9.2-1.20.1.jar
| 13_[c-mod-自动钓鱼Forge版]forgeautofish-6.0.0-1.20.1.jar => [c-mod-自动钓鱼Forge版]forgeautofish-6.0.0-1.20.1.jar
| 14_[c-mod-自然群系指南针]NaturesCompass-1.20.1-1.11.2-forge.jar => [c-mod-自然群系指南针]NaturesCompass-1.20.1-1.11.2-forge.jar
```

增改删后再重新 `rename -w 2 -m add prefix` 确保美观可控