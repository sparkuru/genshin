---
title: "introduction-to-stl"
description: "cpp stl implementation；chapter 01；introduction to stl"
date: "2024-01-10T14:24:00.000Z"
updated: "2024-12-12T03:26:07.000Z"
tags: []
draft: false
layout: "post"
slug: "cpp-stl-notes"
---

## Introduction to SGI-STL

大多数程序员在面对软件开发时，一直都没有一套公认的标准，例如使用的数据结构和算法规范，导致程序员大量时间花费在重复而无意义的劳动上。程序员应当被视作艺术家，他们应当熟练运用高级语言、汇编语言操纵计算机硬件，实现各种天马行空的想象。

## what

cpp 标准模板库，The C++ Standard Template Library（STL）被设计出来建立数据结构和算法的一套标准。stl 主要提供 6 大组件

-   容器（containers）：各种数据结构，比如 vector、list、deque、set、map
-   算法（algorithms）：各类算法，比如 sort、search、copy、erase
-   迭代器（iterators）：简单来讲，迭代器提供了一种按顺序逐个访问某一集合的方法，不需要知道集合的具体数据结构，而由迭代器自发地将其获取
-   仿函数（functors）：单个函数不能被直接拿去操作（例如对某个函数排序），仿函数就是一种在函数原有概念上魔改出的函数，这种函数可以被传递给 STL 算法，可以被排序、查找等
-   适配器（adapters）：可用于对上述组件进行魔改，例如拿到一个迭代器，可以制作出一个迭代器适配器（iterator adapter）。原本迭代器是顺序迭代，则 iterator adapter 就可以被魔改成反向迭代、插入迭代等
-   配置器（allocators），用于负责空间配置和管理，即分配堆内存（allocate heap memory）之类的

![图 1-1](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20240225215900181.png)

如图 1-1 所示，container 通过 allocator 获取数据存储的空间，algorithm 通过 iterator 存储 container 中的内容，functor 结合 adapter 用于协助 algorithm 实现对 container 进行的各种操作（排序、求和什么的）

STL 最初的版本由 Hewlett Packard Company 实现，后续所有 fork 版本都有对应的 HP license 声明。教材着重介绍的是 SGI STL 实现版本，该版本被 gcc 采用，其他的版本还有 P.J.Plauger、Rouge Wave 等，SGL STL 的各种头文件可以在 mingw32 的 `include/c++` 目录下找到，主要分为以下几种

-   cpp 标准规范下的 c 头文件，例如 cstdio、cstdlib、cstring 等
-   cpp 标准库中不属于 stl 的文件，例如 stream、string 等
-   stl 标准头文件，例如 vector、list、map 等
-   hp 规范的 stl 头文件，例如 vector.h、deque.h 等
-   **sgi stl 文件，例如 stl_vector.h、stl_deque.h 等，教材将基于这些文件教予读者学习**
