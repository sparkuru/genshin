# frida-使用范例

get src here：[frida/frida](https://github.com/frida/frida.git)；上手用了 frida，有一种万物皆可 debug 的感觉，动态调试玩起来还蛮有意思的，Android、Linux、Windows 等平台上的动态插桩工具，拦截应用程序的函数调用、监视数据传输以及修改应用程序的行为，从而进行各种各样的分析和测试操作

## installation

frida 可以通过 `pip install frida-tools` 一键安装（支持 python 的全平台）

-   在 Linux 上安装完成后将其添加到环境变量：`export PATH=$PATH:/home/user/.local/bin`，可以写到 `~/.bashrc` 中，执行 `frida --version` 查看版本号

-   在 Windows 上，更推荐使用 venv 虚拟环境来配置 frida 工作环境：

    1.   选择一个应用安装目录，以 `cd E:/reverse/frida` 为例，在该目录下执行：`python -m venv [venv_name]`，自定义环境名，这里起 **frida**；

    2.   要使用 frida 工作时，在 terminal（powershell） 执行：cd `E:/reverse/frida/`，`[venv_name]/Scripts/activate`，成功进入 frida 环境

         ```powershell
         (frida) PS E:\reverse\frida> frida --version
         16.2.1
         ```

    3.   在 `(frida)` 环境下只要执行 `deactivate` 即可退出工作环境

    4.   建议写入 powershell 的配置文件如下：

         ```powershell
         function frida {
             if ($env:VIRTUAL_ENV -and (python -c "import sys; print(sys.prefix == sys.base_prefix)")) {
                 & "$FRIDAPATH\frida\Scripts\frida.exe" $args
             } else {
                 $currentPath = Get-Location
                 Set-Location -Path $FRIDAPATH
                 & ".\frida\Scripts\Activate"
                 Write-Host "`n------------------------------------------------" -ForegroundColor Yellow
                 Write-Host " Activated Frida venv environment | $FRIDAPATH" -ForegroundColor Yellow
                 Write-Host " Type 'deactivate' to exit" -ForegroundColor Yellow
                 Write-Host "------------------------------------------------`n" -ForegroundColor Yellow
                 Set-Location -Path $currentPath
             }
         }
         ```
         
         配置完成后在 terminal 输入 `frida` 即可打开 frida 工作环境（了解一下 python venv 的工作原理，此时很多之前 python pip 包都不可用，当然这也方便创建一个纯 frida 工作环境）

## usage

frida 的运行需要 root 权限

要解析固件、apk 时，需要到 [release](https://github.com/frida/frida/releases/) 中下载 frida-server 对应的 platform 和 structure，例如要解析是 mips linux 固件，则下载 `frida-server-x.x.x-linux-mips.xz`，解压得到 `frida-server` 将其复制到固件中，后台运行之 `sudo /tmp/frida-server &`（需要 root 权限，使用 qemu 模拟时就可以获取 root）

一般都是从解析 apk 应用开始入门（android 的 root 可以参考这篇文章 [android | android-root-records](https://www.majo.im/index.php/wkyuu/258.html)）；需要自行搭建 android studio 环境用于编写 apk 软件

1.   获取到 `frida-server-android-arm`
2.   电脑连接手机，传到 android 上：`adb push frida-server-android-arm /data/local/tmp/frida-server`
3.   使用 adb 进入 android 的 shell：`adb shell`，`su`，运行 frida clent：`/data/local/tmp/frida-server`
4.   在电脑尝试查看 frida 是否成功连接：`frida-ps -U`，该指令列出当前系统正在运行的应用

## refer

1.   引子，[一篇文章带你领悟Frida的精髓（基于安卓8.1）](https://www.freebuf.com/articles/system/190565.html)
2.   frida index，衍生项目、文章等，[dweinstein/awesome-frida](https://github.com/dweinstein/awesome-frida.git)
3.   [frida-all-in-one](https://github.com/hookmaster/frida-all-in-one.git)
4.   