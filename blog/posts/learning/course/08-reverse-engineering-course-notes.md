---
title: "courses | reverse-engineering"
description: "逆向工程课程学习"
date: "2022-10-05T08:50:00.000Z"
updated: "2024-02-21T12:02:46.000Z"
tags: []
draft: false
layout: "post"
slug: "reverse-engineering-course-notes"
---

## 逆向工程

> Windows，i386

## 第一章 - Ollydbg 基础

> 字节序

举例子：`42 == 0x002a`（这里是 2 字节，2a 是一个十六进制字节。00 是高字节，2a 是低字节）

大端序：0x002a，即高低字节放在**对应**高低地址

小端序：0x2a00，即高低字节放在**相反**高低地址

> 单位

**db**， | 位，1 bytes = 8 bits，`0xde`

**dw**，**DWORD**，| 双字节，2 bytes = 16 bits，`0xdead`

**dd** | 四字节，4 bytes = 32 bits，`0xdeadbeef`

## 第二章 - 汇编

> 位数

1 根地址线 = $2^1$ = 2 Bytes

2 根地址线 = $2^2$ = 4 Bytes

...

10 根地址线 = $2^{10}$ = 1024 Bytes = 1 KB

...

32 根地址线（32 位），32 位 = $2^{32}$ = 4294967296 Bytes = 4 GB

> 数据寄存器，32 位

---

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220905094954727.png)

---

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220905095320505.png)

AL，AH：低 8 位，高 8 位

AX：EAX 的低 16 位

EAX：数据寄存器，默认存返回值、累加值，乘法、除法

EBX：存基址

ECX：COUNT，计数器（循环，每次循环会自动减 1），存字符串

EDX：存数据

tips：AX = accumulator，E = Extended

> 通用寄存器

EBP：Extended Base，堆栈基址指针寄存器，基址指针指向栈帧（Stack Frame）的开始地址

ESP：Extended Stack，堆栈栈顶指针寄存器，栈顶指针指向栈帧的栈顶

ESI：Extended Source，操作指向字符串源地址

EDI：Extended Destination，操作指向字符串目标地址

EIP：只能通过 RET，JMP 等操作修改

> 移动栈帧的操作

1. **PUSH EBP**，将当前栈顶指向地址存到 EBP 中，也就意味着 EBP 被移动到原来的 ESP 所在的位置
2. **MOVE ESP**，抬升栈顶位置 ESP，这样更改后的 EBP 和 ESP 就形成一个新的栈帧
3. **PUSHAD**，将寄存器中的值依次压入栈上，并且抬高栈帧，主要作用是保护寄存器信息，即保护现场。顺序为 `EAX，ECX，EDX，EBX，ESP，EBP，ESI，EDI`，
4. **POPAD**，与 3 刚好相反，将栈上内容按 `反序` 弹出给寄存器，并且降低栈帧，从栈上取回寄存器信息，恢复现场
5. **RETN X**，相当于 `POP EIP`，然后 `ADD ESP X`

> 标志寄存器

[标志寄存器](https://github.com/7kms/assembly/blob/master/doc/11-标志寄存器.md)

> 汇编指令集

1. MOV，取地址（寄存器）中的值

  `MOV 目的操作数，源操作数`

  两个操作数的宽度必须一致

2. LEA，取地址本身

3. PHSH，POP

4. PUSHAD，POPAD，将栈上的值依次压入几个通用寄存器

5. JMP，跳转到地址

6. RET，返回到 EIP

7. CALL，机器码 `E8 0E000000` 表示调用当前地址的 `下一条地址 + 0E` 所在的 function

	| 地址           | 机器码              | 值                                      | 解释                             |
	| -------------- | ------------------- | --------------------------------------- | -------------------------------- |
	| 0x0040100B     | E8 **0E**000000     | CALL &lt;jmp.@user32.MessageBoxA&gt;          | 跳转                             |
	| 0x004010**10** | CC                  | INT3                                    | HALT                             |
	| ...            |                     |                                         |                                  |
	| 0x004010**1E** | FF25 08204000(小端) | jmp dword ptr ds:[&lt;user32.MessageBoxA&gt;] | 调用 user32.dll 中的 MessageBoxA |

	这里有一个精妙的是，在 `CALL` 的时候，将下一条地址压栈（该地址也作为函数的 ret 地址）到栈顶，然后根据栈顶的地址 `+0E`

## 第三章 - PE 基础结构

### Windows PE 文件基础

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/20191105010119908.jpg)

> PE：Portable Executable File Format，可移植程序体

1. **虚拟内存地址（VA）**

2. **相对虚拟内存地址（RVA）**，**VA = 模块程序基址 + RVA**

3. **文件偏移地址（FOA）**，就是未动态装载时、存在于外存的文件，只显示**末3位**

	> > FOA，RVA，VA 的关系
	>
	> FOA 某个函数 func：base = 0x400， offset = 0x80，则 func_foa = 0x480
	>
	> RVA 里的 func：base = 0x2000，offset = 0x80，则 func_rva = 0x2080
	>
	> ​	解释为，在即将装载到内存前，需要对齐页粒度，并且导入一些库、函数等
	>
	> VA 里的 func：base = 0x00400000，offset = 0x2080，则 func_va = 0x00402080

4. 数据目录，记录所有可能的数据类型地址，例如 **导入表（PLT）、导出表、属性证书表、重定位表等**

5. 节（section），**.data** 存放初始化的数据，**.code** 存放可执行的代码段

6. 内存对齐，操作系统对内存属性的设置以**页（32位是1000H）**为粒度单位，节在内存中的对其单位必须至少是一个**页**的大小，主要是为了提高管理效率

7. 文件对齐，物理扇区的大小（512字节，200H）作为一个粒度

### PE 文件结构

1. 程序开始：`4D 5A`
2. 找到 `0x0 + 0x3C` 的地方，值为 `B8 00`，代表 PE 的头在 `0xB8`
3. 转到 `0XB8` 的位置，值为 `50 45`，这就是 PE 文件开始的地方
4. `0xB8 + 0X28` 即从 `50 45` 开始，往后 40 bytes 的位置就是程序的入口点

> DOS 头，保留这一程序是为了纪念发明者

1. 用开头 `MZ` 表示 **.exe** 程序
2. 其中包含了标识 PE 的起始地址

> 节

IMAGE_FILE_HEADER.NumberOfSections

固定值，40个字节，节表的大小等于 **节的数量 x 40**

> 节表

即 PE 文件的 Section（.text，.data，.rodata等）的 **index**

PE 文件头部 = DOS头 + PE头 + 节表

PE 文件身体 = 节内容

## 第四章 - PE 基础结构2

1. 导出表：当前应用导出函数给别人用

2. 导入表（Import Table）：PE 文件装载时自带的所需函数表，**记录了一个exe或者一个dll所用到的其他模块导出的函数，用了哪些模块(用了哪些dll)，用了dll的哪些函数**，`RVA = PE头 + 80h` 或者 `PE头 + 78h（这个 78h 的位置是导出表） + 8h（描述使用 4 bytes，前四字节是地址，后四字节是大小）`，Size = （描述使用 4bytes）

> 使用 Winhex 查看内存

打开 `HelloWorld.exe`，在 `winhex` 中 `工具 - 打开 RAM 内存 - 找到 HelloWorld#xxxx` 即可查看当前程序使用的内存。

### 导入表

>  单个导入表结构体共 16 bytes，有

`0000h`，**OriginalFirstThunk** 桥1，里面存了一个地址，存的是 **导入函数名字表（INT）**的地址 

`0004h`，时间戳

`0008h`，链表的前一个结构

`000ch`，指向链接库名字的指针

`0010h`，**FirshThunk** 桥2，也存一个地址，存的是 **导入函数地址表（IAT）**，

在静态时，桥1 和 桥2 指向地址的内容相同，

在动态加载之后，桥2的 IAT 变成正式装载的函数在内存中的入口地址（VA）。动态加载后这一块专门存放动态装载了的函数入口（导入函数的位置是紧挨着的）的地址叫 **导入函数地址表（IAT）**

一个 **双桥结构** 保存了该程序所调用的一个 dll 的具体信息，可以理解为，有几个双桥结构，就表明该 pe 文件调用了几个 dll。

### 导出表

windows 装载器在进行 PE 装载时，会将导入表中登记的所有 DLL 一并载入，然后根据 DLL 的导出表对导入函数的描述修正导入表的 IAT 值。**通过导出表，DLL 文件向调用它的程序或系统提供导出函数的名称、序号、以及入口地址等信息。**  

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20221024090044427.png)

---

一个例子，`RVA_BASE = 0x2000`，`FOA_BASE = 0x800`

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20221024090202815.png)

1. **nName**：从 `0x94c` 开始，`90 21 00 00` 对应 `0x800 + 0x190 = 0x990`，也就对应着 `nName = winresult.dll（用 00 来作为结尾）`

2. nBase 略

3. **NumberOfFunctions**：定位到 `0x954`， `04 00 00 00` 表示该 dll 只有四个**函数**

4. **NumberOfNames**：定位到 `0x958`，`04 00 00 00` 表示该 dll 中，有**名字的函数**的个数只有四个

5. **AddressOfFunctions**：定位到 `0x95C`，`68 21 00 00`，表示导出函数表的开始地址为 `0x2168 - 0x2000 + 0x800 = 0x968`

	然后定位到的 `0x968` 存放的某个函数 func_A 的 RVA，即 `83 11 00 00，0x1183 + VA_BASE = 0x00401183，可以得到函数 func_A 的真实 VA`

	然后接下来三个加上自己，总共四个函数的位置的`指针`是连续的

### 栈

### 加壳

在程序执行前，先执行以获得更好的控制权

1. 在文件的末尾多增加一个 section，将程序的入口地址改成这个 section，在程序加载后会先执行壳里的代码
2. 执行完壳中的内容后，再从壳 section 中回到程序的入口点，加载程序

## 考试

### 实验部分

1. 如何判断一个 PE 文件是合法的

2. kernel32.dll 某两个函数的作用

3. 导入表

	桥1、桥2，静动态变化

4. 导出表

	导出表的遍历、相关结构

5. 栈溢出的概念、理解该图

	![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20221109184139604.png)

6. 壳应用
