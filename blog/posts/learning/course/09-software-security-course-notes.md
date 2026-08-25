---
title: "course | software-security"
description: "courses in learning software security tech, not just in class, what's more is to extra."
date: "2023-05-19T11:28:00.000Z"
updated: "2024-01-19T02:33:46.000Z"
tags: []
draft: false
layout: "post"
slug: "software-security-course-notes"
---

## 软件安全技术

## 20230410

1.   SSL，Secure Socket Layer：安全套接字层，参考 tls，用于通信双方来确认身份。通信时，双方先创建一个 ssl 安全层，用于传输数字证书，随后建立对称加密通道，正式确认双方身份后就可以开始通信了
2.   SSL Heartblood：心脏出血漏洞，在 OpenSSL 1.0 版本中，利用 "心跳扩展功能（heartbeat extension）"，一种用于发送心跳请求，确认对方是否可以进行通信的行为。该漏洞的利用过程如下：
     1.   正常情况下发送正常的心跳请求时，发送如下信息：`if you are there, please reply 3 letters 'hat' to me`，此时对方会回复：`hat` 共 **3** 个字符
     2.   构造恶意请求时，发送如下信息：`if you are there, please reply 500 letters 'hat' to me`，此时对方会回复：`hat ....` 共 **500** 个字符，造成内存泄露
     3.   由于 heartbeat extension 存在于 SSL/TLS 协议的核心组件中，导致旧版本的 SSL 协议不再可靠
3.   软件安全所受威胁 3 大类：软件漏洞、恶意代码、软件侵权
4.   可信任第三方认证技术：例如可信任 CA（证书颁发机构，Certificate Authority），全球可信 CA 数量较少，在操作系统底层就写入了这些可信 CA 的唯一标识，在后续应用的过程中，接收到了可信 CA 的数字证书后，即可被认为通信是安全的
5.   PDRR（或 PD$R^2$） 模型：保护（Protection），检测（Detection），响应（Reaction），恢复（Restore）

## 20230420

1.   shellcode 中一般使用 `0x90  NOP` 来占位置或填充内容，如果捕获到出现大量 `NOP` 指令的情况，就有可能是出现了攻击行为
2.   SEH（结构化异常处理） 异常攻击：Windows 在执行 `int3` 中断时，会让程序 EIP 运行到 **栈上存放 SEH 入口的位置** 执行 SEH 中断处理，若能修改 SEH 的入口为 shellcode，就能在触发 `int3` 中断时执行 shellcode
3.   DWORD Shoot，windows 堆溢出漏洞：覆盖下一个 chunk 的 flink（fd） 和 blink（bk），由于发生解链的时候会有 `node->fd->bk = node->bk`，此时构造 `node->fd = target addr`，`node->bk = shellcode`，就能实现 `*target addr = shellcode` 的任意地址写操作
4.   DEP，数据执行保护，即 NX ENABLED
5.   ASLR，地址空间布局随机化
6.   ABR，数组越界读

## 20230424

1.   早期的病毒会修改受害主机本地的 **hosts** 文件，在其中添加对应的内容例如：`www.huorong.com 127.0.0.1`，此时再去安装杀毒软件的时候，由于访问的是本地环回地址，就会因此出现各种无法访问的情况，也就无法安装杀毒软件

2.   DNS 服务器开放的查询端口是 **53**，使用的协议的 **UDP**，要求访问速度要快；DNS 服务器的 53 端口也会使用 **TCP** 协议进行通信，其目的是保证主从 DNS 服务器之间的数据同步（例如主机 DNS 添加了一个 A 记录，从服务器也要对应同步该 A 记录），称之为 **DNS Zone Transfer**

3.   密码加盐（Password Salting），为密码添加随机字符串后再进行后续处理，主要是为了防止彩虹表攻击等撞库行为

4.   物联网（Internet of Things，IoT）

5.   身份验证机制，**挑战/响应认证方式（Challenge/Response）**，是一种零知识证明方案。指的是

     1.   第一次握手，client 向 server 提出请求（需要提供一个值，例如 **用户 id**），要求进行身份验证
     2.   第二次握手，server 在确定存在该 client 后，返回一个 **随机数**，作为 "提问"
     3.   第三次握手，client 将自身 **用户 id** 与该 "提问" 合并，并生成 hash 指纹，返回给 server 作为应答
     4.   第四次握手，server 将 client 返回得到的 hash 指纹，与 server 本身提取 **用户 id** + **随机数** 进行 hash 指纹比较，若相同，则会向 client 返回 **认证通过**
     5.   整个流程中，没有口令等隐私内容在互联网上传播，即使用 **零知识证明** 完成了身份认证

6.   [参考](https://forsre.cn/pages/aws阿里云腾讯云等内网api地址/)，`169.254.169.254`，是一个 ipv4 空间中作为本地环回地址，云服务商 AWS 就会使用 `http://169.254.169.254` 作为一个特殊的查询地址，这个 API 可以允许云服务器实例访问一些有关自己的元数据信息，

     亚马逊云例如如下查询指令：`curl http://169.254.169.254/latest/meta-data/public-ipv4`，可以获得实例ID、安全组配置等等，利用该地址可以返回服务器信息。

     使用阿里云中可以采取如下查询方式（查询的 api 地址不同）：`curl http://100.100.100.200/latest/meta-data`

     腾讯云：`curl http://metadata.tencentyun.com/latest/meta-data/`

## 20230427

1.   基本输入/输出系统（Basic Input/Output System，BIOS）
     1.   按下电源开关，电源向主板等设备供电，CPU 从地址 FFFF:0000H 开始执行指令，进行 jmp 跳转到 BIOS 的真正启动地址
     2.   BIOS 启动后进行加电后自检（Power-On Self-Test，POST），检查基本硬件设备是否能够正常使用
     3.   硬件自检完成后，从用户设定的启动驱动来加载驱动程序，例如 U 盘启动、硬盘启动等
2.   统一可扩展固件接口（Unified Extension Firmware Interface，UEFI）
3.   主引导记录（Master Boot Record，MBR），BIOS 将 CPU 操作权限交给硬盘后，首先会加载硬盘第一个扇区，最前面 512 个字节的内容，这块内容中存放着关于该硬盘的信息，例如告诉操作系统到哪去获得系统启动盘

## 20230504

1.   当使用 PEeditor 等软件查看一个 exe 可执行文件，发现其 `.text`，`.data` 段的大小为 0x0 的时候，很有可能是因为程序会因为被加壳了而没有真正跑起来，只有程序被真正装载到内存后才会显示出上述段的大小

2.   下面有一串汇编代码

     ```assembly
     mov [ebp - 0x8], eax
     mov eax, [ebp - 0x4]
     cdq
     mov ecx, 3
     idiv ecx
     mov [ebp - 0x8], edx
     ```

     1.   该汇编代码的作用是：`b = a % 3`，
     2.   其中  `cdq`  的作用是扩展 eax 寄存器的符号位；即 `0x00000001` 最高位为 `0` 表示正数；且该扩展会被放入到 edx 寄存器中，值为 `0x00000000`；若 `0xfffffff1` 扩展为 `1`，则 edx 中的值应为 `0xffffffff`
     3.   `idiv` 的作用是进行除法，`idiv ecx` 表示将上述被 `cdq` 扩展后的 **edx:eax** 作为被除数，ecx 作为除数，即 $\frac{edx:eax}{ecx} = eax...edx$，然后将商放入 eax，余数放入 edx
     4.   根据 % 的定义，则取 edx 的值返回给用户

## 20230508

1.   汇编指令中，`jbe`，Jump if Below or Equal；`jge`，Jump if Greater of Equal，的作用都是大于等于就跳转，根据英文释义可以理解到，这两个操作指令的区别其实只有比较的 src 和 dst 的不同，例子如下

     ```assembly
     # 表示比较 edx(src) 和 eax(dst), 当 edx 大于等于 eax, 则执行 jmp addr 
     cmp eax, edx
     jbe addr
     
     # 表示比较 edx(src) 和 eax(dst), 当 eax 大于等于 edx, 则执行 jmp addr
     cmp eax, edx	# 与上一个例子相同, 但是比较的大于号方向不同
     jge addr
     
     # 可以简单理解为, jbe 和 jge 都是用 src 和 dst 进行比较, 根据其英文释义可以看出 cond 是 src < dst 还是 src > dst
     ```

2.   调用约定：**cdecl**，**stdcall**，**fastcall**；编译器在编译的时候，遇到一个 call 函数时，会预先去了解该函数的调用约定是什么，然后根据调用约定来添加汇编指令（例如遇到 fastcall 就是添加 mov；遇到 stdcall 就是添加 push）

     1.   cdecl，从右往左压栈传参（采用 push），由父函数平衡栈帧
     2.   stdcall，从右往左压栈传参（采用 push），由被 call 函数平衡栈帧
     3.   fastcall，寄存器传参（采用 mov），由被 call 函数平衡栈帧；该调用约定使用寄存器传参，可以减少堆栈操作而提高函数调用的性能；不同的编译器使用多少个寄存器来传参的数量是不同的，例如在 windows 下使用的是 win64 约定，允许使用  4 个寄存器传参；而在 linux 下使用的 gcc 约定，可以使用 6 个寄存器传参

## 20230511

1.   Handles 句柄，可以参考 `with open(path, mode = 'rb') as fd` 中的 fd
2.   Windows 注册表，保存操作系统与程序的配置信息
3.   ADVAPI32.dll，与注册表操作有关的 dll 库
4.   浏览器帮助对象，BHO，一种 COM 服务，或者说是接口服务

## 20230515

1.   远程控制工具（Remote Access Trojan，RAT）
2.   僵尸网络（Botnets）
4.   通过泄露 got 的方式，获取 base，然后利用 base 找各种位置的内容，这个过程叫重定位

## 20230518

1.   DLL 加载顺序劫持；由于 DLL 的默认搜索顺序为：应用程序目录，当前目录，系统目录，Windows 目录，PATH 环境目录；故通过劫持这些目录可以实现 DLL 加载劫持

2.   IAT Hooking，导入地址表劫持

3.   Inline Hook，修改实际的函数代码；相较于直接修改 IAT 表，Inline 的主要作用是直接修改被加载的函数中的内容，例如将某个加法操作数，修改成了 `jmp backdoor`，在调用到这个函数时，就会触发 backdoor 的 hook

4.   进程注入，恶意代码注入到正常运行的进程中，以此来绕过一些安全检查，由于恶意代码是依附于正常进程的，一般很难检测到

5.   DLL 注入，类似进程注入，让某个进程强行加载 DLL，原本恶意进程拥有较低的权限，恶意 dll 注入到某些有较高权限的正常进程后，恶意进程就拥有了和正常进程相同的权限，以绕过安全检查；

     其特征是：`CreateRemoteThread()`，这个函数能够创建一个在其它进程地址空间中运行的线程（也称作创建远程线程），以下是 demo

     ```c++
     victimProcess = openProcess();
     hookStartAddress = VirtualAllocEx(victimProcess, ...);	// return address, 在受害进程的内存空间中新增一块区域, 并返回该区域的指针, 后续将往这个区域中写入内容
     WriteProcessMemory(victimProcess, hookStartAddress, injectDLL, ...);	// 往受害进程的新增的这块区域写入恶意 dll
     handle = getMouduleHandle('kernel32.dll');	// 每个进程都有 kernel32.dll
     loadLibraryAddress = getProcessAddr(handle, 'LoadLibraryA');	// 获取 kernel32.dll 中 LoadLibraryA 的位置
     // CreateRemoteThread(handle, wantToExecFunction, execFunctionArgs, ...)
     CreateRemoteThread(victimProcess, loadLibraryAddress, hookStartAddress, ...);	// 让受害进程执行 loadLibraryA, 传入的参数是之前写入的 恶意dll 的开始地址
     ```

6.   在 ida 中发现函数调用方式： `call ds:LoadLibraryA`，这里的 ds，即为 Data Segment

7.   进程替换，将可执行文件重写到一个运行进程的内存空间，且该恶意代码与被替换的进程有相同的特权级

     ```c++
     CreateProcess(..., "svchost.exe", ..., CREATE_SUSPENDED, ...); // 创建一个 svchost 进程, 这里使用了一个 CREATE_SUSPENDED, 表示将进程一创建就先挂起
     ZwUnmapViewOfSection(...);	// 先将刚才 svchost 对应的内存空间转变为可写的
     VirtualAllocEx(..., ImageBase, SizeOfImage, ...);	// 先将恶意代码装载到内存中, 然后在下面将这块内存作为载体, 其数据再写到 svchost 的内存空间
     writeProcessMemory();	// 将恶意代码写入到刚才 svchost 的内存空间
     for (i = 0; i < NumberOfSections; i++) {
         WriteProcessMemory(..., section, ...);	// 循环写恶意代码
     }
     SetThreadContext();	// 修改 svchost 程序开始的入口点
     ResumeThread();	// 恢复 svchost 进程, 即开始运行该 svchost
     ```


## 20230522

1.   软件开发（SDL）核心安全需求：
     1.   保密性
          1.   确定哪些数据应当采用什么加密算法；
          2.   口令不能被明文存储在后端，必须采用散列函数进行加密存储；
          3.   传输账户信息等敏感内容的时候必须采用安全传输协议（例如 SSL/TLS）；
          4.   系统日志文件不应当出现敏感或易被解读的敏感信息。
     2.   完整性；主要是确保系统能按照预期的功能工作
          1.   在输入一些表单信息的时候，需要对输入的数据集进行一些身份验证，防止一些注入攻击等
          2.   系统功能的模块应当有备份以及校验和，防止被篡改，参考 windows 下的 dll 备份，以便使用者能验证模块的准确性和完整性
     3.   可用性；
          1.   高并发，负载均衡
          2.   防止 DoS 攻击
          3.   异地容灾
     4.   可认证性；
          1.   一些可认证需求，例如实名认证，单点登录支持等
     5.   授权；访问控制，最小授权
     6.   可审计性；日志必须精确记录信息，例如身份、时间戳等；日志保留时间必须符合要求。
2.   数据的加密；为了隐藏一些配置文件信息，例如网络特征等
     1.   凯撒加密
     2.   XOR 处理，可以视作一种对称加密
     3.   Base64 加密，每 6 位用于处理一个字符，因为 $2^{6} = 64$，所以叫 Base64 加密

## 20230525

1.   软件安全设计原则

     1.   减少软件受攻击面
     2.   最小授权原则，例如 windows 的 UAC
     3.   权限分离原则
     4.   纵深防御原则
          1.   防火墙
          2.   入侵检测，日志，
          3.   数据加密

2.   威胁建模

3.   网络应对措施；网络行为的攻击基本流量属性包括 IP 地址、TCP 以及 UDP 端口，域名等；安全人员可以依据这些特征来配置安全策略；例如将某个恶意网站的域名重定向到本地一个无害的 ip，这种技术叫 DNS 沉洞 （sinkhole） 技术

4.   对抗检测（Operations Security，OPSEC）；

     1.   域前置技术（Domain Fronting）

          一个 https 访问中，若远程端点被禁用了，可以在 https 实际访问该远程端点的包外层套一个合法的域，当客户端向 dns 服务器发起访问的时候，由于外面套的是一个合法的 dns，则会返回合法的 ip，但是本机却不用这个合法的 ip，而是访问在 https 中真正要访问的节点。这种技术通常用来躲避审查。

## 20230529

1.   病毒自身的脫殼
     1.   從原始程序入口點（Original Entry Point，OEP）開始運行程序；此時的 OEP 指向的地方叫脫殼存根
     2.   病毒自身因爲加殼，無法讓 windows 直接使用導入表來進行，所以會大量利用 `LoadLibrary` 和 `GetProcAddress` 來動態裝載自身所需要的 Library
     3.   尾部跳轉（tail jmp）：在病毒加載完必要的環境信息后，在尾部會使用 jmp 或者 call 進入到程序真正開始的地方
2.   去除程序的混淆
     1.   程序作者自製的一種殼，在解密時經常使用 `VirtualAlloc` 函數來分配虛擬内存，然後將要處理的程序放在這個地方；可以使用 ollydbg 動態調試時，在程序將真正要運行的放入到上述所説的虛擬内存中后，將對應的内存 dump 出來即可

## 20230601

1.   查殺引擎的使用
     1.   文件簽名：傳入一個 `trojan.js` 文件給查殺引擎時，其首先會驗證 hash，若能匹配到特徵，會直接從數據庫中返回曾經分析的結果
     2.   特徵值檢測：為 `trojan.js` 文件添加一些注釋，即修改了文件的簽名，此時有的殺毒引擎會通過檢測病毒的特徵值來確定病毒的情況
2.   病毒沙箱；一種能夠檢測出病毒在其中執行時使用過的資源，連接的網站等内容的模擬環境，通常將病毒放入到沙箱中進行分析，隨後再將特徵值編寫成查殺脚本添加到殺毒引擎中

## exam

1.   注意看實驗的内容，包括理論課上和實驗課裏的
2.   SDL 每個階段要做的事：设计，实施阶段
3.   需求階段；軟件安全開發核心安全需求：CIA 等
4.   設計階段；如何設計防止 sql 注入？如何数据净化，p202 - p203
5.   作業；
     1.   第一次作業；p73 第 6 題；
     2.   第二次作業；除了 SSRF；還應該關注 **2021 OWASP TOP 10** 相較於 2020 版本，有哪些新增的内容，關注這些新增的内容，理解其原理、防禦機制等
6.   另一本書，惡意代碼分析實踐
     1.   DLL 注入、進程替換
     2.   關注使用到的函數，及其參數
     3.   ida 中能看懂是如何對數據加密和解密的，例如如何進行 xor 解密，使用的 key 是什麽，要能分析出 key 的值
     4.   實驗内容必看
