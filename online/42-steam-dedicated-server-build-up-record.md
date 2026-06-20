# steam-dedicated-server-build-up-record

steam 平台常见游戏服务器构建记录

## Left 4 Dead 2

### 搭建服务端

1. 安装 steamCMD

   1. 推荐将 `~/steam` 目录作为总工作目录：`mkdir -p ~/steam/SteamCMD`
   2. 安装 32 位包
      1. `sudo dpkg --add-architecture i386`
      2. `sudo apt-get update`
      3. `sudo apt-get install -y lib32gcc1 lib32stdc++6 libc6-i386 libcurl4-gnutls-dev:i386`
   3. 安装 SteamCMD
      1. `cd ~/steam/SteamCMD`
      2. `wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz`
      3. `tar -zxvf steamcmd_linux.tar.gz`
      4. 启动：`./steamcmd.sh`，输入 `quit` 退出

2. 安装 l4d2 服务端

   1. 创建游戏服务器文件夹：`mkdir -p ~/steam/servers/l4d2`

   2. 上一步成功安装 SteamCMD 后 在 `~/steam/SteamCMD` 目录下输入：`./steamcmd.sh` 即可进入 steam 的 shell

   3. 接下来的操作在 steam 的 shell 中操作，前面会加一个 *steam&gt;*

      ```bash
      steam>force_install_dir ~/steam/servers/l4d2	# 注意路径
      steam>login anonymous							# 匿名登陆
      steam>app_update 222860 validate				# 这里的222860请参考参考链接2来确定l4d2的下载请求id
      ```

      然后等待下载完成

   4. 也可以

      ```shell
      ~/steam/SteamCMD/steamcmd.sh \
      	+force_install_dir ~/steam/servers/l4d2 \
      	+login anonymous \
      	+App_update 222860 validate \
      	+quit
      ```

3. 创建一个 steam 组，后面的配置文件需要一个组的 id，这里可以在 steam 中找到组，创建一个自己的组，具体方式自助

### 配置服务端

上一步最后显示 `Success! App '222860' fully installed.` 后就可以开始下面的步骤了

1. `mkdir -p ~/steam/servers/l4d2/00_workdir/scripts`，`cd ~/steam/servers/l4d2/00_workdir/scripts`，`touch server.cfg`

2. 配置该 `server.cfg` 文件如下：

   ```nginx
   hostname "Left 4 Dead 2"	# 服务器名，用英文
   sv_steamgroup xxx			# xxx 是你的组id
   sv_steamgroup_exclusive 1	# 设置服务器为组私有
   sv_allow_lobby_connect_only 1	# 允许通过组服务器来连接
   sv_tags hidden	# 就是不在浏览服务器里显示
   
   ## 我的
   hostname "l4d2"
   hostport 10086
   sv_tags "hidden"
   sv_gametypes "coop"
   sv_cheats 0
   sv_voiceenable 0
   sv_allow_lobby_connect_only 0
   sv_region 4
   sv_visiblemaxplayers 4
   sv_steamgroup "42392770"
   sv_steamgroup_exclusive 1
   sv_consistency 0
   exec banned_user.cfg
   exec banned_ip.cfg
   ```

3. 软链接：`ln -s ~/steam/servers/l4d2/00_workdir/scripts/server.cfg ~/steam/servers/l4d2/left4dead2/cfg/server.cfg`

注意需要放行相关端口的 tcp 和 udp

### 运行服务端

运行脚本 `touch ~/steam/servers/l4d2/00_workdir/scripts/stat-l4d2.sh` 如下：

```shell
#!/usr/bin/env bash

home=/home/wkyuu
work_dir=$home/steam/servers/l4d2/
scripts_dir=$work_dir/00_workdir
binary_path=$work_dir/srcds_run

$binary_path \
    -game left4dead2 \
    -condebug \
    +ip 0.0.0.0 \
    -insecure \
    -nomaster \
    +exec server.cfg \
    +map $(cat $scripts_dir/scripts/map)

# -game	            指定游戏是left4dead2
# -insecure	        关闭VAC，建议关，不然可能有冲突
# +hostport	        对应开放的端口，不写就默认是27015
# -condebug	        输出debug信息
# -nomaster	        隐藏服务器连接
# -maxplayers num	最大游戏人数
# +exec server.cfg	按照写好的server.cfg脚本执行
# +map xxx	        指定一张地图启动
```

如果显示  *.steam/sdk32/steamclient.so: cannot open shared object file: No such file or directory*，则执行 `ln -s ~/steam/SteamCMD/linux32/steamclient.so ~/.steam/sdk32/`

显示 *Connection to Steam servers successful. VAC secure mode is activated.*  则表示启动成功

### 连接服务端

在上述步骤完成后，在求生之路2中打开控制台，输入 `connect 你的服务器ip:对应端口`，即可连接。如果连接不上，注意确保服务器对应端口的的TCP和UDP都要能通。

### cfg 详细设置

```html
hostname "XXX" 主机名字
sv_allow_lobby_connect_only "0" 大厅连接
mp_disable_autokick 1 自动踢人
z_difficulty "Normal" 游戏难度
sv_cheats 1 允许作弊
sv_Infinite_ammo 0   设为1就是无限弹药
z_respawn_distance 5 僵尸重生距离
z_respawn_interval 2 僵尸重生延迟

z_tank_health 7000  坦克生命值
z_tank_incapacitated_health 0 坦克无法行动生命值
tank_attack_range 100  坦克攻击距离
tank_burn_duration_vs 10 坦克燃烧时间（烧完就死了）
z_tank_throw_interval 1 坦克投掷石头延迟
tank_throw_min_interval 1 坦克投掷石头最小延迟
z_witch_health 500 巫婆生命值，原始为1000
z_hunter_health 200 猎人生命值
hunter_pounce_max_loft_angle 90 猎人跳跃角度
hunter_pz_claw_dmg 15 猎人爪子伤害值
z_hunter_speed 900 猎人速度
z_exploding_health 100 胖子生命值，原始为50
z_exploding_speed 450 胖子速度，原始为175
z_gas_speed 400 烟鬼速度，原始为210
boomer_vomit_delay 0 
z_vomit_interval 0 胖子喷射胆汁延迟
sb_vomit_blind_time 0 胖子胆汁致盲时间
z_vomit_fade_duration 3 胆汁褪色所需时间
z_vomit_fade_start 3 胆汁褪色时刻（被喷到的第三秒）
z_vomit_range 600 胖子喷射胆汁距离
z_vomit_boxsize 2 胆汁贴图大小
z_vomit_maxdamagedist 650 最大喷射距离
z_gas_health 200 烟鬼生命值
Smoker_escape_range 500 烟鬼逃生距离
tongue_hit_delay 2 烟鬼蓄舌延迟
tongue_miss_delay 2 烟鬼再次蓄舌延迟
tongue_range 5000 烟鬼舌头长度，初始为750

sv_visiblemaxplayers 8 服务器可见最大玩家数
maxplayers 8 最大玩家数

first_aid_heal_percent 1 医疗包恢复生命百分比，这里为1，即100%
first_aid_kit_max_heal 500 医疗包恢复生命数
first_aid_kit_range 200 医疗包恢复生命距离
first_aid_kit_use_duration 1 医疗包恢复生命所需时间（秒）
```

### 游戏常用指令

按 `~` 打开控制台

1. 打开第三人称模式：`bind g "thirdpersonshoulder 1"`，按 `g` 即可打开

2. 改名：`setinfo name 要改的名字`

3. 其他控制台指令

   | 指令                                     | 说明                                    |
   | ---------------------------------------- | --------------------------------------- |
   | sb_takecontrol Ellis/Nick/Rochelle/Coach | 换人                                    |
   | upgrade_add Incendiary_ammo              | 获得燃烧子弹的升级效果                  |
   | upgrade_add explosive_ammo               | 获得爆炸子弹的升级效果                  |
   | upgrade_add laser_sight                  | 获得激光瞄准的升级效果                  |
   | give adrenaline                          | 肾上腺素针                              |
   | give defibrillator                       | 电震仪器                                |
   | give first_aid_kit                       | 医药包                                  |
   | give pain_pills                          | 药丸                                    |
   | give gascan                              | 汽油红桶                                |
   | give rifle                               | M16步枪                                 |
   | give rifle_ak47                          | AK47步枪                                |
   | give pistol_magnum                       | 玛格南手枪                              |
   | give katana                              | 东洋武士刀（仅限第1、2、4大关战役可用） |
   | give grenade_launcher                    | 榴弹发射器                              |
   | give upgradepack_explosive               | 爆炸子弹升级铁盒                        |
   | give upgradepack_incendiary              | 燃烧子弹升级铁盒                        |

### extra

1. 快速覆盖方案

   ```shell
   rsync \
   	-av \
   	--ignore-existing \
   	~/steam/servers/l4d2/00_workdir/root/* \
   	~/steam/servers/l4d2/left4dead2
   ```

2. 装插件

   1. 推荐以下插件目录（源自 [求生之路 2 插件下载](https://www.sg7z.com/2966.html)）：

      ```powershell
      linux版（6968-1155）（必须先启用这个）
      windows版（6968-1155）（必须先启用这个）
      可选-修复类（v1.0）（修复出现多次换弹动作）（HarryPotter）
      可选-修复类（v1.0.0）修复口水伤害和范围异常（洛琪）
      可选-修复类（v1.0.0）修复生还者血量大于女巫伤害时导致的问题（豆瓣酱な）
      可选-修复类（v1.0.3）物品掉落发光问题修复（Mart）
      可选-修复类（v1.1）（修复部分情况下角色对话跟模型不一致）（TBK Duy, Harry）
      可选-修复类（v1.1）（修复部分梯子导致的崩溃）（SilverShot and Peace-Maker）
      可选-修复类（v1.2.5）（修复生还者过关后装备或属性混乱）（sorallll）
      可选-修复类（v1.5）修复更改最大弹夹后换弹鬼畜（SilverShot）
      可选-修复类（v2）（修复SG552开镜换弹鬼畜）（bullet28）
      可选-修复类（v2.0.1）（修复有相同的幸存者角色时牛撞不动的问题）（Lux）
      可选-修复类（修复HUD闪屏）（游戏运行时添加无效）
      可选-修复类（修复玩家正在连接时不刷特感）（v1.0.9）（sorallll & Psyk0tik （Crasher_3637））
      可选-修复类（修复生还者闲置过关后下一关开始时延迟五秒自动闲置的问题）
      必选-修复类（v1.0）修复地图过渡数据遗产（IA NanaNana）
      必选-修复类（v2.0.1）（修复电击器救起存活的幸存者）（Lux）
      必选-修复类（v2.8b）（解决linux系统CFG不加载）（SilverShot, Peace-Maker）
      必选-功能类扩展（sourcescramble.ext）（v0.7.1.4）
      必选-功能类插件（WeaponHandling）（v1.0.6）（Lux）
      必选-功能类插件（left4dhooks）（v1.158）（SilverShot）
      必选-功能类插件（原生投票函数库）（v0.4）（Powerlord, fdxx）
      必选-功能类插件（原生键值函数库）（v0.4）（fdxx）
      自选-8角色共存（v1.9.12）（DeatChaos25, Mi123456 & Merudo, Lux, SilverShot）
      自选-8角色共存（修复玩家在短暂时刻救援关变成NPC）
      自选-M60正常化（可更换弹夹和拾取弹药）（v1.0.7）+榴弹发射器拾取弹药（v1.0）（Lux）
      自选-传送或处死长时间不进终点安全屋的玩家（v1.2.0）（sorallll）
      自选-击杀或爆头和黑枪提示和关闭队伤（1.0.5）（豆瓣酱な）
      自选-后备弹药插件（豆瓣酱な）
      自选-多人插件superversus1.8.15.5改（v1.11.8）（DDRKhat, Marcus101RR, Merudo, Lux, Shadowysn, sorallll）
      自选-幸存者倒地使用马格南（v1.0.2）（sorallll）
      自选-幸存者捡起主武器自动获得激光升级（ZZH,凌凌漆）
      自选-幸存者死亡和被制服提示（v1.4.9）（豆瓣酱な-死亡提示嫖至sorallll）
      自选-幸存者黑白发光（v2.0.2）（Lux）
      自选-扔投掷物提示（v1.0.8）（Mart）
      自选-换图类（投票换图）（v1.1）（fdxx, sorallll, HatsuneImagine）
      自选-排行榜插件（v2.21.28）（豆瓣酱な）（HUD的include提供者为 sorallll）
      自选-根据人数设置医疗物品倍数（v1.0.5）（豆瓣酱な）
      自选-点燃或打爆物品提示（v1.0.7）（Mart）
      自选-爬梯时可开枪（v1.0）（Lux）
      自选-玩家指令！vt投票插件（v2.4.5）（豆瓣酱な）
      自选-生还者触发警报车提示（v2.0）（Eyal282）
      自选-管理员娱乐菜单（v1.2.3b）（sorallll）
      自选-管理员指令！kb踢出全部电脑生还者（v1.0.0）（豆瓣酱な）
      自选-管理员菜单开关旅游模式（v1.1.0）（豆瓣酱な）
      自选-管理员菜单更改游戏模式（v1.3.3）（豆瓣酱な）
      自选-管理员菜单更改游戏难度（v1.0.2）（豆瓣酱な）
      自选-管理员菜单更改生还免控（v1.3.1）（豆瓣酱な）
      自选-管理员菜单设置生还免伤（v1.3.5）（豆瓣酱な）
      自选-设置倒地次数为0时阻止不正常的心跳声（Sir, 豆瓣酱な）（内有作者原版）
      自选-防止服务器人数不足而关闭（v1.0.9）（AtomicStryker）
      ```

      可以在 [这里](https://pan.baidu.com/s/1IKhCcT4o09Fj9-N4WWMIcA?pwd=5ytj) 直接获得，找 plugins.zip 文件

   2. 选择自己喜欢的插件，将其中的 left4dead2/addons 文件夹中的内容直接添加到 `~/steam/servers/l4d2/left4dead2` 即可

   3. 配置管理员：随意进入一场游戏，在控制台中输入：`status`，可以得到一串类似 *STEAM_1:1:125637774* 的内容，将其添加到文件 `~/steam/servers/l4d2/left4dead2/addons/sourcemod/configs/admins_simple.ini` 的末尾，例如

      ```ini
      ...
      
      "STEAM_1:1:125637774"     "99:z"
      ```

      然后进入从控制台进入服务器游戏，在聊天框输入 `!admin`​ 出现管理员目录即代表成功

3. 装第三方图

   1. 使用 [GCFScape](https://nemstools.github.io/pages/GCFScape-Download.html) 解压地图 vpk 文件，得到一个 root 文件夹，一般结构如下

      ```powershell
      root
      |-- addoninfo.txt
      |-- maps
      |-- materials
      |-- missions
      |-- models
      |-- scripts
      `-- sound
      ```

      其实也是文件夹 `~/steam/servers/l4d2/left4dead2/` 的目录结构，装第三方图本质上就是把 vpk 文件解压放到对应的地方，让游戏服务器在启动时能够找到对应的文件就行了

   2. 将其上传到 `~/steam/servers/l4d2/left4dead2/` 目录（一般都有很多文件，小文件传输不方便，建议压缩后上传再解压）

## Unturned

### 搭建服务端

1. 创建游戏服务器文件夹：`mkdir -p ~/steam/servers/unturned`

2. 上一步成功安装 SteamCMD 后 在 `~/steam/SteamCMD` 目录下输入：`./steamcmd.sh` 即可进入 steam 的 shell

3. 接下来的操作在 steam 的 shell 中操作，前面会加一个 *steam&gt;*

   ```bash
   steam>force_install_dir ~/steam/servers/unturned	# 注意路径
   steam>login anonymous								# 这里需要登陆账号
   steam>app_update 1110390 validate
   ```

   然后等待下载完成

### 配置服务端

上一步最后显示 `Success! App '1110390' fully installed.` 后就可以开始下面的步骤了

1. `mkdir -p ~/steam/servers/unturned/00_workdir/scripts`，`cd ~/steam/servers/unturned/00_workdir/scripts`，`touch server.cfg`

2. 以下是文件 `ExampleServer.sh` 的说明，主要启动游戏的文件为 `~/steam/servers/unturned/ServerHelper.sh`

   1. 有两种启动模式：`ServerHelper.sh +InternetServer/ServerId` 或 `ServerHelper.sh +LanServer/ServerId`
   2. `ServerId` 指的是在 `unturned/Servers` 目录下独立的文件夹，每个文件夹对应一个 `ServerId`，也就是装着独立的存档
   3. 支持对每个存档独立配置命令：直接编写 `unturned/Servers/ServerId/Server/Commands.dat` 或者 `ServerHelper.sh -CommandName/arg0/arg1/... +LanServer/ServerId`
   4. 游戏端口的配置，每个 `ServerId` 需要两个 **连续的** port（只需指定第一个 port，会自动使用 +1 的port），第一个 port 用于查询、第二个 port 用于连接服务器
   5. 常用服务器配置信息 `unturned/Servers/ServerId/Server/Commands.dat`，[参考](https://docs.smartlydressedgames.com/en/stable/servers/server-hosting.html)：
      1. `Name XYZ`，指定服务器的名字
      2. `Port num`，指定服务器开放的端口
      3. `Owner SteamId`，指定服务器 admin 的 id
      4. `Password XYZ`，指定服务器连接密码
      5. `Perspective Both/First/Third`，设置可使用的人称视角
      6. `Cheats`，指定是否允许 admin 作弊

   执行 `~/steam/servers/unturned/ExampleServer.sh` 将启动一个服务器示例并保存到 `unturned/Servers/Example` 文件夹，可以进一步进行魔改

3. 配置 GSLT，目的是允许服务器被互联网发现，好友可以收藏以及方便连接；[参考](https://docs.smartlydressedgames.com/en/stable/servers/game-server-login-tokens.html)

   1. 打开 https://steamcommunity.com/dev/managegameservers，登录账号
   2. 在下方 *创建一个新的游戏服务器帐户* 处填入 appid：304930，可以添加备注，点击创建
   3. 可以得到登陆令牌，将其填入到 `unturned/Servers/ServerId/Config.json` 里的 `Browser.Login_Token` 值；还可以同时修改其他展示内容

### 运行服务端

运行脚本 `touch ~/steam/servers/unturned/00_workdir/scripts/stat-unturned.sh` 如下：

```shell
#!/usr/bin/env bash

work_dir=~/steam/servers/unturned
scripts_dir=$work_dir/00_workdir
binary_path=$work_dir/ServerHelper.sh

$binary_path \
    +LanServer/example \
```

如果显示  *.steam/sdk32/steamclient.so: cannot open shared object file: No such file or directory*，则执行 `ln -s ~/steam/SteamCMD/linux32/steamclient.so ~/.steam/sdk32/`

显示 *Connection to Steam servers successful. VAC secure mode is activated.*  则表示启动成功

## 参考链接

1. [基于Linux(Ubuntu)系统搭建求生之路2(L4D2)服务器](https://www.maxyang.world/ubuntu-l4d2-server/)
2. [服务端下载id](https://developer.valvesoftware.com/wiki/Dedicated_Servers_List)
3. [番外：在CentOS上搭建求生之路2服务器](https://www.ceplavia.com/2019/11/18/2019-11-18_番外：在CentOS上搭建求生之路2服务器)
4. [求生之路2公网服务器开服开三方图手册](https://bgm.tv/blog/279122)
5. [使用 steamcmd 搭建游戏服务器](https://blog.ginshio.org/2021/steam_apps/)
6. [搭建求生之路2服务器和插件分享](https://www.alsaces.cn/posts/314a5cd5/)
7. [Bind keys](https://developer.valvesoftware.com/wiki/Bind)
8. [l4d2 指令集](https://left4dead.fandom.com/wiki/Console_commands)
9. [unturned 开服](https://www.tudoumc.com/post/1610.html)
10. https://steamcommunity.com/sharedfiles/filedetails/?id=1586156054
11. https://steamcommunity.com/sharedfiles/filedetails/?id=1562197537
12. https://steamcommunity.com/sharedfiles/filedetails/?id=3443708208