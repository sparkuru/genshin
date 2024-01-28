# Android Root Record

**请留意：本文旨在进行 Android 设备逆向攻防学习和交流，需要使用 root 权限进行部署和攻击。所涉及的设备为本人自行购入并使用。请读者在下载任何非法软件后的 24 小时内将其删除，对于由本文可能引起的任何后果，概不负责。本人强烈建议读者不要尝试获取和使用本文中的技术。**

记录 Android 设备 root 过程，设备 Redmi Note 11T pro+，本文提供 Magisk 方案~~和 kernelSU 两种方案~~

>   手机解锁前的碎碎念

目前的国产手机搭载的系统，即便是很接近类原生，但是都会有某程度上的本地化定制。换言之，解锁 BL 之后可以尝试刷系统，目前国产对解 BL 比较友好的品牌：一加、联想、摩托罗拉、小米；如果不在乎相机性能的话，你可以先物色一些机型，然后到 XDA 看看该机型的支持的 ROM 、Recovery ，或者直接去一些知名的 ROM 官方：Lineage OS 、PixelExperience 、PixelOS

**总结一下**：解 BL、刷 root、刷第三方 ROM、刷第三方 Recovery、刷机之后相机会不太好使（厂商调教过），但是可以试试装 Google Camera、如果不玩需要「 Play 游戏」支持的游戏，可以考虑放弃 Google 框架，转投 microG，个人建议 RAM 12G 以上

## root

**无论是选择 Magisk 还是 KernelSU，都需要先解 BootLoader**；20240127更新国内厂商解锁现状，[参考](https://github.com/KHwang9883/MobileModels/blob/master/misc/bootloader-kernel-source.md)：

-   小米（红米）：支持解锁，但需要通过地狱级难度的答题测试，解锁 ROOT 保修；
-   OPPO（真我 realme）：部分机型支持解锁，需要申请，名额有限。要求机型上市时间必须超过 3 个月，同时需要 OPPO 官方开放该机型的深度测试。支持解锁 ROOT 保修，前提是设备可以正常回锁；
-   一加：支持解锁，不需答题申请，方式简单。解锁 ROOT 保修；
-   vivo（含 iQOO）：不支持解锁；
-   华为、荣耀：不支持解锁；
-   魅族：不支持解锁，但官方开放不完整 ROOT ，可以替换为 Magisk；
-   中兴（努比亚、红魔）：不支持解锁；
-   三星：支持解锁，方式简单，但是有 KNOX 物理熔断机制，解锁之后无法恢复；
-   索尼：大部分支持解锁，但是需要申请获取解锁码，部分机型解锁后有功能缺失；
-   联想（摩托罗拉、拯救者）：支持解锁，方式简单

### BootLoader

手机在启动时需要引导程序（以下称为 `boot.img`，请注意，新的 A/B 分区的系统使用的是 `init_boot.img`，如果你不确定自己使用的是 boot 还是 init_boot，去网上查），手机在出厂时，为了保证手机安全（增加被他人非法破解的成本），会对 bootloader 进行上锁，其作用就是确保手机在启动时引导的是官方的 `boot.img`；目前的 root 方案主要为 magisk 和 kernelSU 两种；

-   在 magisk 中，其操作是魔改 `boot.img` 变成 `boot-magisk-patch.img`（主要实现的方式可以理解为：先启动 Linux init，再启动 magisk，最后启动 system，整个操作过程相当于中间人实现，这也就能解释为什么只要在 fastboot 下重新刷回官方 boot 就能安全去掉 root 权限了，即插即用），然后让 bootloader 在启动时装载 `boot-magisk-patch.img`，由于引导程序都被修改了，意味着可以在系统中增加 su 来使用 root 权限，也就实现了 Android 设备的 root（**基于用户空间**）
-   在 KernelSU 中，其基本逻辑为替换操作系统的内核，其操作也是先修改 `boot.img` 为 `boot-kernelsu-patch.img` 并引导启动，然后使用工具将官方的 kernel 修改成 KernelSU 提供的魔改过的 kernel，由于是 **基于内核空间** 进行操作，往往拥有更高的权限

可以发现，以上两种方案都需要先解锁 BootLoader，因此想要进行 Android 设备的 root，首先确保自己的设备能够解锁 BootLoader，小米设备（2024 年以前）解锁方法如下：

1.   下载 [解锁工具](https://www.miui.com/unlock/index.html)，连接手机，按照要求操作
2.   等待 7 天后，顺利进行解锁，**由于解锁会清除手机数据，记得备份重要数据（第三方软件）：通讯录，短信，各种视频图片等**
3.   下载安卓调试工具，[SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools?hl=zh-cn)，解压备用（文件路径不能含有中文名）

在 2024 年以后，官方的解锁条件变成 **答题 + 社区签到**，难度较高，因此建议采用其他还提供 bl 解锁的厂商进行 root 实践，例如联想、一加、索尼等

### tee

安卓设备的 TEE（Trusted Execution Environment，可信执行环境）是一种安全执行环境，通常由硬件和软件组成，用于保护敏感数据和执行安全操作。TEE 提供了一个与主操作系统隔离的环境，即在设备的处理器中创建一个安全的执行环境，独立于主操作系统，这个环境被设计成难以被恶意软件或攻击者访问，从而保护其中存储的敏感信息。

指纹支付通常依赖于设备中储存的生物特征信息，例如用户的指纹模板。这些信息需要得到高度的保护，以防止未经授权的访问。TEE 提供了一个安全的执行环境，可以存储和处理这些生物特征信息，同时避免主操作系统或其他应用程序的干扰。

**目前除了小米手机解锁后 TEE 不会出问题，其他品牌都会出问题。**一加解锁后 TEE 必掉，TEE 处于 **"假死"** 状态，即 TEE 检测到解锁后主动拒绝工作，导致例如微信的指纹支付模块直接失效。目前比较流行的操作是，利用软件自动为设备自动输入支付密码，**这种行为其实有风险，需要机主自行决断**。

### Magisk

>   获取 root

1.   pc 连接手机

2.   **备份手机的 boot.img**：在 **设置 - 关于手机 - 全部信息 - MIUI 版本**，找到对应的 rom 版本，例如 `13.2.2.0(TLOEUXM)`，就到 [这里](https://xiaomirom.com/series/) 找到对应手机的对应版本 `13.2.2.0(TLOEUXM)` 下载完整 rom，得到 tgz 文件，一般需要解压两次，然后在 `images` 目录下找到 `boot.img` 文件；或者看文末的 boot 提取方法，尝试提取手机的 boot

3.   将 `boot.img` 复制到手机内存中任意位置，这里以 `Download` 文件夹为例

4.   下载最新的 release.apk，然后在手机上安装 `magisk.apk`

5.   在手机上 **打开 magisk - Magisk 安装 - 选择并修补一个文件 - 找到刚才的 boot.img - 开始**，修补完成后，会在相同目录下生成一个 `magisk_patched-26400_xxxxx.img`

6.   在 pc 上将以上 `boot.img` 和 `magisk_patched-26400_xxxxx.img` 文件放到 platform-tools 同目录下，最终目录拓扑如下

     ```bash
     .
     |-- ...
     |-- adb.exe
     |-- boot.img
     |-- fastboot.exe
     |-- magisk_patched-26400_xxxxx.img
     |-- ...
     `-- sqlite3.exe
     ```

7.   在 platform-tools 目录下打开终端；

     1.   输入 `.\adb.exe reboot bootloader`，此时手机会自动重启并进入 fastboot 模式
     2.   输入 `.\fastboot.exe devices` 可以发现识别到了设备
     3.   输入 `.\fastboot.exe oem lks` 可以查看联发科设备的解锁状态（0 表示解锁，1 表示未解锁）；高通是 `.\fastboot.exe oem device-info`（Device unlocked：true 表示解锁，false 表示未解锁）
     4.   输入 `.\fastboot.exe flash boot magisk_patched-26400_xxxxx.img` 开始刷写替换的 boot，出现两个 OKAY 即可完成
     5.   输入 `.\fastboot.exe reboot` 重启设备

8.   手机重启后，打开 Magisk，提示需要安装环境并重启，确定后设备自动重启，至此获取 root 完成

>   一些优化，以下是默认已经完成了通过 magisk 获取了 root

1.   Magisk Delta（即 Magisk Canary，26404），下载 app-release.apk 并安装到手机；进入 Magisk Delta，修复环境即可，**后续全部 magisk 操作交给这个新的红色狐狸面具**

2.   有的软件会尝试检测本机有没有 root 然后拒绝服务（例如金融、银行 app 类），因此需要隐藏 root；在 magisk 应用中，**右上角齿轮 - 隐藏 Magisk 应用 - 一路确定和创建快捷方式**，然后 **开启 zygisk 勾选框 - 遵守排除列表 - 配置排除列表 - 将想要排除掉的 app 勾选上（注意应用可以下拉全部选完）**，建议在下面安装了 shamiko 后采取白名单模式（只给 LSPosed、ES explorer 等应用获取 root 尝试）

     检测 google play 完整性：**google play store - 头像 - 设置 - 关于 - 连续点击 play store 版本直到进入开发者模式 - 常规 - 开发者选项 - 检查完整性**，主要观察返回的对话框中的 labels 属性：
     1.   包含 `MEETS_DEVICE_INTEGRITY` 表示一般性正常状态。应用正在由 Google Play 服务提供支持的 Android 设备上运行。设备通过了系统完整性检查，并且满足 Android 兼容性要求。
     2.   包含 `MEETS_STRONG_INTEGRITY` 表示应用正在由 Google Play 服务提供支持且具有强有力的系统完整性保证（如由硬件提供支持的启动完整性保证）的 Android 设备上运行。设备通过了系统完整性检查，并且满足 Android 兼容性要求。
     3.   仅含有 `MEETS_BASIC_INTEGRITY` 表明应用正在通过了基本系统完整性检查的设备上运行。设备不满足 Android 兼容性要求，未被批准运行 Google Play 服务。例如，设备可能正在运行无法识别的 Android 版本、有已解锁的引导加载程序，或者没有经过制造商的认证。

3.   使用 adb 工具，输入 `.\adb.exe shell`，然后输入 `su`，如果出现了 permission denied，就到 magisk 里看超级用户列表，为 `[SharedUID] Shell` 添加运行 root 权限，**方便后续 adb 救砖**

4.   MRepo，可以从中下载各类模块，模块管理工具

5.   Shamiko，提供更好的 root 授权服务；zip 文件复制到手机，在 Magisk 的 **模块 - 从本地安装 - 选择 zip 文件 - 安装 - 重启手机**

6.   LSPosed，用于魔改系统，zip 文件安装方式同上

>   如果刷模块导致各种问题（例如界面崩溃无法点开 app、无法开机），以下是几种解决方案

-   如果能直接打开 magisk 对模块进行管理，则直接删除掉对应的模块即可
-   如果无法开机，但是还能进入 fastboot 模式
    1.   进入 fastboot 模式
    2.   在同目录下另起一个终端，输入 `.\adb.exe wait-for-device shell "magisk --remove-modules"`，目的是下次手机重启那一刻，就通过 adb 让 magisk 卸载所有 modules
    3.   保持之前那个终端不关闭的情况下，另一终端 `.\fastboot.exe reboot`
    4.   然后排查 modules
-   如果无法有效打开 magisk 界面，例如 launcher 一直崩溃（一般是因为修改了动画，字体等导致 launcher 不兼容），但是能进入系统
    1.   首先尝试按照上文刷回 `boot.img`
    2.   正常开机后，手机打开 magisk 应用界面，终端输入 `.\adb.exe shell "dumpsys window | grep mCurrentFocus"`，目的是获取 magisk 应用的启动名，例如 magisk 返回了 `mCurrentFocus=Window{966f077 u0 com.topjohnwu.magisk/com.topjohnwu.magisk.ui.MainActivity}`，则应用的启动名称就是 `com.topjohnwu.magisk/com.topjohnwu.magisk.ui.MainActivity`
    3.   此时可以先退回手机桌面，然后终端尝试输入 `.\adb.exe shell "am start -n com.topjohnwu.magisk/com.topjohnwu.magisk.ui.MainActivity"`，发现手机打开了 magisk 应用
    4.   再刷入 `magisk.img`，正常开机，由于 launcher 一直崩溃，直接在 adb 中用上文的命令打开 magisk 就能管理模块了
-   如果可以直接进入 `.\adb.exe shell` 并且通过 `su` 指令可以进入 root 模式，直接以 root 身份进入 `/data/adb/modules` 目录，删除相应模块即可
-   TWRP Recovery 模式（前提是需要手机型号有适配的 twrp 工具，而 note 11tpro 正好没有，下文的 oneplus ace 3 有）
    1.   在 twrp.me 中下载与手机型号对应的 twrp.img 到 pc 上，这里以放到和 adb.exe 同目录为例
    2.   使手机进入 fastboot 模式，主要有以下两种方式
         1.   使用 adb：`.\adb.exe reboot bootloader`
         2.   手机完全关机，按住 **电源按钮** 和 **音量 down 按钮**，不同机子可能不同，具体去查自己机子的进入方式
    3.   输入 `fastboot flash recovery .\twrp.img` 将 recovery 分区修改成 twrp 分区；**如果是已经拥有了 root 权限**，也可以直接通过：先通过 `.\adb.exe push twrp.img /sdcard/twrp.img`，然后通过 `.\adb.exe shell` 进入系统手动装载：`su`、`dd if=/sdcard/twrp.img of=/dev/block/bootdevice/by-name/FOTAKernel`
    4.   进入 recovery 模式以启用 twrp，有以下两种方法
         1.   **通过手机直接进入 recovery 模式**，例如同时按住 **音量 up** 和 **音量 down**
         2.   输入 `.\fastboot boot twrp.img` 进入 recovery 模式
    5.   在 twrp 界面中，**高级 - 文件管理 - 进入 /data/adb/modules 文件夹**，排查删除出问题的模块，例如`rm miuiflash`

其实根据上述几种方法，**其核心无非就是要删除出问题的模块**，最优先是直接通过 magisk 删除模块，其次是在 adb 模式下删除模块，最后才是通过第三方引导的方式删除模块，读者可以通过这种思路来排查救砖

在前文的优化中，提到了一个将 `[SharedUID] Shell` 允许获取 root 的步骤，其原因是 magisk 在隐藏 root 并通过 Shamiko 开启白名单模式下，会自动拒绝所有不在白名单下的应用获取 root，而 shell 就是 `.\adb.exe shell` 执行时使用的用户，此时输入 `su` 自然会被 permission denied，这也就是提前为其添加 root 权限的原因

### magisk uninstall

由于 magisk 的原理就是修改启动引导由原来的 `boot.img` 为 `magisk.img`，因此只需要逆着将 `magisk.img` 修改为 `boot.img` 就可以恢复了

1.   连接 pc 和手机，进入 platform-tools 目录并打开终端
2.   输入 `.\adb.exe reboot bootloader`，令手机进入 bootloader 模式
3.   找到之前备份的 `boot.img`，刷入原生 boot：`.\fastboot.exe flash boot '.\boot.img'`
4.   重启 `.\fastboot.exe reboot`，此时系统复原到刷入 magisk 之前的情况

### ~~KernelSU~~

~~目前 KernelSU 的生态还不够完善，很多好用的模组都是基于 LSPosed 进行开发，可以等到将来可以和 magisk 不分伯仲了再切换成 KernelSU 也不迟~~

## others

### extract boot by tool

现在一些 rom 下载下来是进行了加密的，将其放在一个 payload.bin 文件内，需要使用工具来解包：

1.   提取所有文件：`.\payload-dumper-go.exe -o .\img .\payload.bin `
2.   仅提取 boot.img 文件：`.\payload-dumper-go.exe -p boot -o .\img .\payload.bin`
3.   仅提取 init_boot.img 文件：`.\payload-dumper-go.exe -p init_boot -o .\img .\payload.bin`

### extract boot by hand

由于一加系列的手机对于解锁十分开放（仅在 fastboot 下输入 `fastboot flashing unlock` 即可解锁），笔者弄了一台来体验，这里以一加 ace 3 刻晴定制机为例，因为手机目前（20240307）还未放出官方 rom 的资源，而本机使用的出厂系统是 `PJE110_14.0.0.320(CN01)`，而目前市面上还未流出该版本的 rom 包（20240315 更新：已经向设备推送了 502 新系统的更新，但是据社区反应，续航有所下将，秉持着出厂系统就是最好的系统的原则，还是先把本系统完整提取后以备不时之需，顺便进行 root），没法从中提取出 boot.img 用于 magisk 修补，故采用以下方式进行 boot 的提取

-   （失败）没法直接提取其中的 boot.img，尝试直接在手机内提取 boot
    1.   电脑连接手机，打开 usb 调试，使用 `adb shell` 进入手机系统
    2.   进入 boot 存放的目录：`cd /dev/block/by-name`（Android 14 是这样，不同的手机可能有不同路径）
    3.   可以看到 `boot_a`、`boot_b`、`init_boot_a`、`init_boot_b` 字样，即系统采用的是 A/B 分区，有两个内核，共享数据和设置，目的是在使用 a 时 b 在后台更新，下次重启直接使用 b 来重启以完成系统的升级，
    4.   使用 `ls -l boot_a` 可以看到 *lrwxrwxrwx 1 root root 16 1970-01-02 09:59 boot_a -> /dev/block/sde13*，即动态链接到了 `/dev/block/sde13`，继续查看之：`ls -l /dev/block/sde13`，得到权限为 *brw-------*，无 root 无法提取：`dd if=/dev/block/sde13 of=/sdcard/Download/boot_a.img`，返回 *dd: /dev/block/sde13: Permission denied*，无解
-   （推荐）使用 TWRP 恢复模式提取 boot
    1.   需要有专门适配的 twrp，这里有幸找到了第三方制作的 [twrp for oneplus ace 3](https://t.me/colorospro/215)，下载完成后解压，拿到 `TWRP-14-Aston-Color597-V1.2.img` 文件
    2.   **注意：刷入非官方的恢复模式引导镜像（将无法恢复），以及进行 root 都将导致系统无法正常接收官方系统更新**；
    3.   手机连接电脑后，使用 `.\adb.exe reboot bootloader` 进入 fastboot 模式，输入：`.\fastboot.exe flash recovery ./TWRP-14-Aston-Color597-V1.2.img` 将 twrp 刷入 recovery 模式**（必须使用官方原厂数据线才能识别到 fastboot 模式）**
    4.   在 fastboot 模式下，按音量下键切换到 recovery 模式，按 power 键确认进入 twrp（如果手机有解锁密码就输入解锁密码）；然后 "**备份 - 选择 boot 和 init boot - 存储位置选择内置存储 - 滑动滑块确认备份**"，回到主界面点击重启到系统
    5.   使用电脑从手机存储中以下位置：`TWRP\BACKUPS\serialno\xxx-xxx-xxx` 找到 `boot.emmc.win` 和 `init_boot.emmc.win` 文件传输到电脑上存档备份，看到后缀不是 img，不必担心，这是用于恢复的，如果后续出现开不了机，进 twrp 将这两个文件恢复即可**（如果不确定手机会不会变砖，且可能会要用到 twrp 来恢复，则在刷机前需要先将手机的解锁密码关闭）**
    6.   继续进入 recovery 模式（保持电脑连接手机），此时在 `adb.exe shell` 可以发现成功进入了命令行，而且是 root 权限，此时可以手动提取 boot 和 init boot 了
         1.   按照上文 dd 提取流程，进入 boot 目录：`cd /dev/block/by-name`，找到 boot_a 指向文件，将其提取保存：`dd if=/dev/block/sde13 of=/sdcard/Download/boot_a.img`；
         2.   顺便还要保存一份 init_boot_a 文件，这个才是后续要刷入的真正的 boot 文件：`ls -l init_boot_a` 返回 *lrwxrwxrwx 1 root root 16 1970-01-14 22:32 init_boot_a -> /dev/block/sde32*；将其提取出来：`dd if=/dev/block/sde32 of=/sdcard/Download/init_boot_a.img`
         3.   提取完成后重启之，两个文件放在了手机目录：`Download` 下，备份之，之后使用 magisk 修补和 root 的流程就如前文所述；**特别需要注意的是**，在修补和刷入 boot 时，选择的文件是 `init_boot.img`（8 MB 大小） 而不再是 `boot.img`，指令如下：`.\fastboot.exe flash init_boot magisk_patched-26400_xxxxx.img`，如果出问题了，就找到刚才备份的 `init_boot.img`，刷回 init_boot 分区

### build twrp

get twrp src here：[TeamWin/android_bootable_recovery](https://github.com/TeamWin/android_bootable_recovery.git)，build doc：[How to compile TWRP touch recovery](https://xdaforums.com/t/dev-how-to-compile-twrp-touch-recovery.1943625/)

## refer

1.   [小米 rom 下载](https://xiaomirom.com/series/)
2.   [Motorola 通用官方解锁 Bootloader 教程](https://bbs.ixmoe.com/t/topic/25562)
3.   [荣耀手机 ROOT 失败，以后可能直接买非国产手机了](https://fast.v2ex.com/t/963863?p=1#r_13479161)
4.   [一加手机官方 ROM 下载](https://yun.daxiaamu.com/OnePlus_Roms/)
5.   [一加手机 magisk 模块下载](https://yun.daxiaamu.com/files/magisk%E6%A8%A1%E5%9D%97/)
6.   [Android 手机如何提取系统内核(boot.img 镜像文件提取)](https://blog.csdn.net/weixin_43890033/article/details/114966941)
7.   [Extract Boot.img Directly from Device Without Downloading Firmware](https://droidwin.com/extract-boot-img-directly-from-device-without-downloading-firmware/)
8.   sony twrp，[TWRP for Sony Xperia X Compact](https://twrp.me/sony/sonyxperiaxcompact.html)
9.   [手机硬核折腾指南：没刷机包也能获取 Root 权限？](https://www.bilibili.com/video/av1351763175)
10.   [payload-dumper-go 提取 boot（payload 提取 boot.img）](https://magiskcn.com/payload-dumper-go-boot)