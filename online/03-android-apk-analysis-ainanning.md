# android reverse apk analysis ainanning

手机里有个城市通应用叫 "爱xx"，发了颠一样狂扫我是不是用了代理，用安卓就狂扫，用 ios 就乖。客户有需求的时候，通过代理的内网联系到我，届时我需要时刻连接回家对服务器进行运维，不开代理就变相增加了我的成本。目标：看一下 apk 是怎么实现代理检测的

![图-1](E:\Pictures\markdown\image-20240308183423971.png)

## main

### hominid

多种反编译方式

1.   使用 jadx 反编译该应用，值得一提的是 kali for wsl 中，使用 jadx 需要先将 apk 移动到 `/usr/share/jadx/bin` 中，然后输入 `jadx -D ./jadx-ainanning ainanning.apk`；能够得到 `jadx-ainanning/resources` 资源文件、`jadx-ainanning/sources` 由 smali 反编译成 java 的文件集合
2.   或使用 ghidra 创建项目，导入 ainanning.apk，选择 file system 模式，然后 export 到某个文件夹 `ghidra-ainanning/decompile`，但是似乎只能提取出 `ghidra-ainanning/decompile/resources` 资源文件
3.   再或者使用 apktool，命令行输入：`apktool d -f -o ./apktool-ainanning ainanning.apk` 一步到位全部提取

在 `sources/com/coralline/sea/s3.java`（打开了代码混淆，看起来有点吃力）下可以发现，看来管的还不少

![图-2](E:\Pictures\markdown\image-20240307164132888.png)

通过 jadx 的注释可以发现，这些反编译源码来自于 *loaded from: assets/RiskStub.dex*，即 `resources/assets/RiskStub.dex` 文件，可以使用 `d2j-dex2jar -o dex2jar-riskstub.jar assets/RiskStub.dex` 来获取 jar 包，当然反编译的源码是可看但是编辑是没用的，要编辑还得转换成 smali 源码（java 和 smali 的关系类似 c 和 汇编语言）：`d2j-dex2smali -o dex2smali-riskstub assets/RiskStub.dex`，编辑完 smali 源码后，转回 dex，最后再转回 apk 文件，得到的 smali 源码如下：

![图-3](E:\Pictures\markdown\image-20240307181406647.png)

再次将 smali 源码转换成 java 源码，可得以下内容

![图-4](E:\Pictures\markdown\image-20240307181324067.png)

显然要改起来是有难度的，于是想办法找真正起作用的函数去 hook 掉，兜兜转转发现以下内容

![图-5](E:\Pictures\markdown\image-20240307182736749.png)

如图所示，真正起作用的是右边的 `d = new JSONObject(c7.b(c2)).optJSONObject("checker")`，会逐个检查列表中的项目，具体流程请见后文

显然可以在右侧 `:L2` 下添加一个 `retuan-void`，或者直接删除掉这一串 smali 码，修改完成后，将其重新编译回 dex：`d2j-smali -o re-RiskStub.dex dex2smali-riskstub/*`，然后替换掉 `apktool-ainanning/assets/RiskStub.dex`，再重新编译回 apk：`apktool b -o re-ann.apk apktool-ainanning`，不过大概率会出各种奇奇怪怪问题，大多数是依赖的问题

### three body people

当然建议使用大佬汉化好的工具 [APK Easy Tool v1.59.2 - Windows 下使用的安卓逆向工具](https://www.52pojie.cn/thread-1411747-1-1.html)

![图-6](E:\Pictures\markdown\image-20240307185415997.png)

下图为使用该软件搭配 vscode 的 smali2java 插件实现的，前文了解一下原理差不多得了，做事还是要讲究效率

![图-7](E:\Pictures\markdown\image-20240307203610027.png)

1.   （一般流程）首先在手机上，使用 MT 管理器提取应用，并且记录其签名值 hash1，将 apk 传到工作目录
2.   如图所示，先 **反编译** 得到 apk 内容于 `1-Decompiled APKs/ainanning.apk` 目录，同时顺便 **提取** 一份于 `3-Extracted APKs/ainanning.apk` 目录
3.   **打开反编译目录** 找到 `1-Decompiled APKs/ainanning.apk/assets/RiskStub.dex`，拖入 **smali** 选项卡 **反编译 smali**
4.   在 vscode 中找到 `s3.smali`（诚然，如果没有 jadx 一把将所有 dex 都 java 化了，仅仅使用文本匹配工具大概率是比较难找到的），右键 *Decompile This File*（需要 vscode 插件 smali2java 支持）
5.   根据 java 源码修改 smali 源码，修改完成后，**回编译 smali** 得到 `6-Smali/RiskStub.dex`，将其复制并替换到 `1-Decompiled APKs/ainanning.apk/assets` 以及 `3-Extracted APKs/ainanning.apk/assets` 目录下同名文件
6.   执行 **回编译**，得到 `2-Recompiled APKs/re-ainanning.apk`，导入到手机，使用 MT 管理器查看新的签名值 hash2
7.   将 `3-Extracted APKs/ainanning.apk/classes.dex` 进行 **反编译 smali**，这里如果没问题的话，会有签名 hash1 硬编码于这些 smali 文件里，直接替换成 hash2 即可，然后 **压缩** 于目录 `4-Zipped APKs/ainanning.apk`
8.   将最后压缩打包好的 apk 安装到手机：`adb install ainanning.apk`

想象中一切都很美好，当然也就止步于想象了。以上流程对付老版本、或者不注重反逆向的 apk 可能有用，但是对于付费进行反逆向的 apk 就难了。首先就所谓硬编码 hash 值这一步就不太可能出现，检索到当前应用使用的是 [梆梆加固企业版](https://www.cnblogs.com/2014asm/p/14547218.html)，其会对每个文件都添加唯一指纹，如果不顾一切要逆向是有可能实现的，但是凡事要讲究成本和回报，就和对 rsa 进行破解一样，理论上终究是理论上。

## idk

在文本编辑器编写了 `abc.java`，编译成 `abc.class`，多个 `xxx.class` 打包成 `abc.jar`；在 Android 上，`abc.jar` 会被转换成 `abc.dex` 文件，然后 Android 的 ART（Android Runtime）就能运行 `abc.dex`，`abc.smali` 是 `abc.dex` 反编译出的字节码，可以类比成由 c/cpp 语言编译出的文件使用 objdump 查看其汇编代码

![图-8](E:\Pictures\markdown\image-20240308164604095.png)

使用 jadx-gui 打开 apk 文件，可以方便一次性直接查看源码（自带 smali2java）；或者原始一点，首先 `dex2jar -o RiskStab.jar RiskStab.dex`，然后解压 `unzip -d class RiskStab.jar`，搭配 vscode 插件 Decompiler 可以直接看 java 源码

通过 `grep -ir "proxy"`，得到以下返回

```bash
....
coralline/sea/q3.java:  public static final String i = "VpnProxyChecker";
coralline/sea/q3.java:    super("vpnproxy", 15);
coralline/sea/q3.java:      JSONObject jSONObject = e0.a("vpnproxy");
coralline/sea/q3.java:                    a("upload", "vpnproxy", jSONObject1.toString());
coralline/sea/s3.java:      a.put("1017", "httpproxy");
coralline/sea/s3.java:      a.put("1018", "vpnproxy");
coralline/sea/s3.java:      c.put("httpproxy", "请勿使用https代理!");
coralline/sea/s3.java:      c.put("vpnproxy", "请勿使用vpn代理!");
....
```

意味着相关检测代码在大概率与 `q3.java` 这些文件有关，下面贴出源码

![图-9](E:\Pictures\markdown\image-20240308210810755.png)

其中 *JSONObject jSONObject = e0.a("vpnproxy");* 这行代码中的函数对象如下：

![图-10](E:\Pictures\markdown\image-20240308180828906.png)

转换成 java 源码得：

```java
import org.json.JSONObject;

public class test {
    public static synchronized JSONObject convertJSONObject(JSONObjec e0, String key) {
        synchronized (e0) {
            JSONObject jsonObject = e0.optJSONObject(key);
            if (jsonObject == null) {
                jsonObject = new JSONObject();
            }
            return jsonObject;
        }
    }
}
```

函数创建了一个 JSONObject 对象，对象命名为 vpnproxy，函数使用 `Enumeration<NetworkInterface> enumeration = NetworkInterface.getNetworkInterfaces()` 枚举了手机设备上的所有网络接口相关信息，将正在启用的网络接口集合起来写入 hashmap 对象中，然后不断枚举 hashmap 中的内容，由于返回的是接口名称等信息，通过 `str.contains("tun") || str.contains("ppp") || str.contains("pptp")` **判断接口的名称是否包含常见的代理网卡名称来确定是否用了代理**，说实话感觉蛮古老的，如果我有能力修改网络接口的名称是不是直接给他干掉了

通过 `adb shell` 进入手机终端，在开启了小猫以后，输入 `ifconfig` 确实可以查看网络接口名为 tun0 的，此时手机上打开该应用，成功跳出 **检测到代理** 字样的对话框；关闭小猫以后，看不到 tun0 接口，手机再打开应用就没再检测到代理了

![图-11](E:\Pictures\markdown\image-20240308183524164.png)

由于通过破解的方式需要和签名斗智斗勇，该想想盘外招了，由此大概可以提出以下几种解决方案：

-   为该应用的 `NetworkInterface.getNetworkInterfaces()` 功能返回空或特定信息
-   为 tun0 接口改名，可以到小猫 for Android 的仓库里看看有没有
-   root 后编写模块限制住该应用乱扫手机隐私的行为

从 图 - 9 中还能看到与 *vpn_credibility = 0.8D*（可信度） 有关的字眼，结合与 *upload* 不难理解，这玩意不仅扫描到代理不让你用，还会尝试把手机中与代理有关的信息上传

## sh1t

使用 frida 插桩来监控应用（需要 root 权限），可以参考这篇文章 [android | android-root-records](https://www.majo.im/index.php/wkyuu/258.html) 对设备进行 root；从 [release](https://github.com/frida/frida/releases/) 处获取 `frida-server-x.x.x-android-arm` 文件；

kali 上可以安装 adb 调试工具：`sudo apt install adb`，由于 kali for wsl 官方 distribution 没有添加 usb 支持，需要自行进行内核编译添加 usb support，并在启动时指定编译出的 kernel，参考另一篇文章 [app | windows-terminal](https://www.majo.im/index.php/wkyuu/36.html)；**如果嫌麻烦的话**，直接使用 kali in vmware，在连接手机设备后选择连接到虚拟机即可（需要在虚拟机设置中添加 USB 控制器）

电脑连接手机，将其传输到手机里：`adb push frida-server-android-arm64 /data/local/tmp/frida-server`，运行之：`su`，`/data/local/tmp/frida-server`；frida 的环境的配置可以参考 [app | frida-handbook](https://www.majo.im/index.php/wkyuu/334.html)，使用 `frida-ps -U` 可以获取手机当前正在运行的任务

1.   手机上打开 ainanning，`adb shell` 进入系统，输入：`dumpsys window windows | grep mCurrentFocus` 以获取当前应用的信息 *com.cloudbae.lovenanning/com.cloudbae.lovenanning.home.view.HomeActivity*，当前应用名为：**com.cloudbae.lovenanning**
2.   

## references

1.   书籍（1），[移动应用安全与风控，FIGHTING安](https://bbs.kanxue.com/thread-277381.htm)
2.   文章（1），[对某 apk 的一次插桩记录](https://www.kanxue.com/chm.htm?id=19079)
3.   文章（2），[一篇文章带你领悟 Frida 的精髓（基于安卓8.1）](https://www.freebuf.com/articles/system/190565.html)
4.   教程（1），[Android Studio 开发 apk 参考](https://www.cnblogs.com/AnneHan/p/9815645.html)
5.   