---
title: "linear-algebra"
description: "线性代数，301 大纲要求。"
date: "2023-11-29T11:54:00.000Z"
updated: "2024-08-20T02:41:12.000Z"
tags: []
draft: false
layout: "post"
slug: "linear-algebra-notes"
---

## 线性代数

>   按照 301 要求的标准复习

## 快速记忆

>   行列式

1.   余子式 $M_{ij}=\underline{\hspace{3em}}$，代数余子式 $A_{ij}=\underline{\hspace{3em}}$，行列式的值 $|A|=\underline{\hspace{3em}}$
2.   行列式的转置 $\begin{vmatrix}1&2&3\\4&5&6\\7&8&9\\\end{vmatrix}^{-1}=\underline{\hspace{3em}}$，值改变吗？$\underline{\hspace{3em}}$；
3.   行列式中任意两行交换 $\begin{vmatrix}1&2\\3&4\end{vmatrix}=\underline{\hspace{3em}}$；行列式中有任意两行相同 $\begin{vmatrix}1&2\\1&2\end{vmatrix}=\underline{\hspace{3em}}$
4.   行列式的数乘 $2\begin{vmatrix}1&2\\3&4\end{vmatrix}=\underline{\hspace{3em}}=\underline{\hspace{3em}}=\underline{\hspace{3em}}=\underline{\hspace{3em}}$；推论：行列式中任意两行成比例 $\begin{vmatrix}1&2\\2&4\end{vmatrix}=\underline{\hspace{3em}}=\underline{\hspace{3em}}$
5.   行列式的加减  $\begin{vmatrix}1+2&3+4\\5&6\end{vmatrix}=\underline{\hspace{3em}}\stackrel{交换律}{=}\underline{\hspace{3em}}$
6.   行列式中某行的倍数与加减 $\begin{vmatrix}1&2\\3&4\end{vmatrix}\stackrel{r_{2}-3r_{1}}{=}\underline{\hspace{3em}}$

>   矩阵

1.   矩阵的加法：两个矩阵的形状相同时，$\begin{pmatrix}1&2\\3&4\end{pmatrix}+\begin{pmatrix}5&6\\7&8\end{pmatrix}=\underline{\hspace{3em}}$

2.   矩阵的数乘：$2\begin{pmatrix}1&2\\3&4\end{pmatrix}=\underline{\hspace{3em}}$，注意和行列式的数乘区分开

3.   矩阵的乘法：$m\times s$ 形状的矩阵乘以 $s\times n$ 形状的矩阵，得到 $\underline{\hspace{3em}}$ 形状的矩阵，表示为 $(m\times s)\cdot(s\times n)=\underline{\hspace{3em}}$；所得矩阵中第 $a_{ij}$ 的值由 $i$ 行和 $j$ 列对应元素相乘再累加；矩阵的乘法有交换律吗？（即 $AB \underline{\hspace{1em}}BA$）

4.   分块矩阵

     分块矩阵 $A=\begin{vmatrix}A&*\\O&B\\\end{vmatrix}$，其中 $A$ 矩阵是 $m$ 阶、$B$ 矩阵是 $n$ 阶的，$*$ 表示任意矩阵，$O$ 表示零矩阵，有以下结论

     1.   $\begin{vmatrix}A&{*}\\O&B\\\end{vmatrix} = \begin{vmatrix}A&O\\{*}&B\\\end{vmatrix} = \underline{\hspace{3em}}$，$\begin{vmatrix}{*}&A\\B&O\\\end{vmatrix} = \begin{vmatrix}O&A\\B&{*}\\\end{vmatrix} = \underline{\hspace{3em}}$
     2.   $\begin{pmatrix}A&O\\O&B\\\end{pmatrix}^{n}=\underline{\hspace{3em}}$
     3.   $\begin{pmatrix}A&O\\O&B\\\end{pmatrix}^{-1}=\underline{\hspace{3em}}$，$\begin{pmatrix}O&A\\B&O\\\end{pmatrix}^{-1}=\underline{\hspace{3em}}$
     4.   $\begin{pmatrix}\lambda_{1}&O&O\\O&\lambda_{2}&O\\O&O&\lambda_{3}\end{pmatrix}^{-1}=\underline{\hspace{3em}}$，$\begin{pmatrix}\lambda_{1}&O&O\\O&\lambda_{2}&O\\O&O&\lambda_{3}\end{pmatrix}^{n}=\underline{\hspace{3em}}$；

5.   分块矩阵的运算

     1.   $\begin{pmatrix}A_{1}&B_{1}\\C_{1}&D_{1}\\\end{pmatrix}+\begin{pmatrix}A_{2}&B_{2}\\C_{2}&D_{2}\\\end{pmatrix}=\underline{\hspace{3em}}$，$\begin{pmatrix}A_{1}&B_{1}\\C_{1}&D_{1}\\\end{pmatrix}\begin{pmatrix}A_{2}&B_{2}\\C_{2}&D_{2}\\\end{pmatrix}=\underline{\hspace{3em}}$
     2.   $\lambda\begin{pmatrix}A&B\\C&D\\\end{pmatrix}=\underline{\hspace{3em}}$
     3.   $\begin{pmatrix}A&B\\C&D\\\end{pmatrix}^{T}=\underline{\hspace{3em}}$

>   转置矩阵、方阵的行列式、伴随矩阵以及逆矩阵

矩阵：$A=\begin{pmatrix}1&2\\3&4\\\end{pmatrix}$，转置矩阵：$A^{T}$，行列式（方阵）：$|A|$，

伴随矩阵：$A^{*}=\begin{pmatrix}(-1)^{1+1}*4&(-1)^{1+2}*3\\(-1)^{2+1}*2&(-1)^{2+2}*1\\\end{pmatrix}$

1.   $(A+B)^{T}=\underline{\hspace{3em}}$，$(\lambda A)^{T}=\underline{\hspace{3em}}$，$(AB)^{T}=\underline{\hspace{3em}}$，若 $\underline{\hspace{3em}}$，则 $A$ 为对称矩阵
2.   $|A^{T}|=\underline{\hspace{3em}}$，$|AB|=\underline{\hspace{3em}}$，$|\lambda A|=\underline{\hspace{3em}}$
3.   $AA^{*}=\underline{\hspace{3em}}=\underline{\hspace{3em}}$，$|A^{*}|=\underline{\hspace{3em}}$ （与方阵的关系），$(AB)^{*}=\underline{\hspace{3em}}$，$(\lambda A)^{*}=\underline{\hspace{3em}}$，$(A^{*})^{*}=\underline{\hspace{3em}}$
4.   若 $AB = E$，则 $A$ 与 $B$ 的关系？$\underline{\hspace{3em}}$；若 $A$ 可逆，则 $|A|$ 要求？$\underline{\hspace{3em}}$；求 $A^{-1}$ 的方法 $\underline{\hspace{3em}}$
5.   $(\lambda A)^{-1}=\underline{\hspace{3em}}$，$(AB)^{-1}=\underline{\hspace{3em}}$，$(A^{T})^{-1}=\underline{\hspace{3em}}$，$(A^{*})^{-1}=\underline{\hspace{3em}}$，$|A^{-1}|=\underline{\hspace{3em}}$，$A^{*}=\underline{\hspace{3em}}$

>   利用线性代数解方程

1.   基本思想

     一个简单的二元一次方程组，使用线性代数表示如下
     $$
     \begin{aligned}
     \begin{equation}
     \left\{
     \begin{aligned}
         &x + y = 5 \\
         &2x - 3y = 12
     \end{aligned}
     \right.
     \end{equation}
     
     \Leftrightarrow
     
     \begin{pmatrix}x_{1}+2x_{2}\\2x_{1}-x_{2}\end{pmatrix}
     \=
     \begin{pmatrix}3\\1\end{pmatrix}
     
     \Leftrightarrow
     
     \begin{pmatrix}1&2\\2&-1\end{pmatrix}
     \begin{pmatrix}x_{1}\\x_{2}\end{pmatrix}
     \=
     \begin{pmatrix}3\\1\end{pmatrix}
     
     \Leftrightarrow
     
     AX=B
     \end{aligned}
     $$
     此时要求出 $\begin{pmatrix}x_{1}\\x_{2}\end{pmatrix}$，只需要解 $AX=B$ 即可；

     1.   由 $AX=B\Leftrightarrow A^{-1}\cdot AX=A^{-1}B\Leftrightarrow X=A^{-1}B$；
     2.   组成 $(A, E)$ 联合矩阵，经过初等变换得出 $A^{-1}$；
     3.   最后 $X=A^{-1}B$ 即可解出原方程组的解

     对于 $AX=B$，$A$ 称为系数矩阵，$(A, B)$ 称作增广矩阵，

     1.   若 $B=\begin{pmatrix}0\\0\end{pmatrix}=0$，则 $AX=B$ 是齐次线性方程组；
     2.   若 $B\neq0$，则 $AX=B$ 称作非齐次线性方程组

2.   行阶梯形、行最简形

     1.   行阶梯形

          1.   阶梯线下方全是 $\underline{\hspace{3em}}$；
          2.   每级阶梯占 $\underline{\hspace{3em}}$ 行，可以占多列；

     2.   行最简形

          1.   得是行阶梯形
          2.   每级阶梯第 $1$ 个元素是 $\underline{\hspace{3em}}$；
          3.   每级阶梯第 $1$ 个元素所在列的其余元素为 $\underline{\hspace{3em}}$

          举例如下：

          1.   $\begin{pmatrix}1&2&3&4\\0&5&6&7\\0&8&0&0\end{pmatrix}$，有 $2$ 个阶梯，$\underline{\hspace{3em}}$ （是/不是）行阶梯形；
          2.   $\begin{pmatrix}1&2&3&4\\0&0&6&7\\0&1&0&0\end{pmatrix}$，阶梯线下方不全为 $0$，$\underline{\hspace{3em}}$ （是/不是）行阶梯形；
          3.   $\begin{pmatrix}1&2&3&4\\0&5&6&7\\0&0&8&9\end{pmatrix}$，$\underline{\hspace{3em}}$ （是/不是）行阶梯形；
          4.   $\begin{pmatrix}1&2&3&4\\0&0&5&6\\0&0&0&0\end{pmatrix}$，$\underline{\hspace{3em}}$ （是/不是）行阶梯形；
          5.   $\begin{pmatrix}1&2&0&3\\0&0&1&4\\0&0&0&0\end{pmatrix}$，$\underline{\hspace{3em}}$ （是/不是）行阶梯形，$\underline{\hspace{3em}}$ （是/不是）行最简形；

3.   解齐次线性方程组

     一个多元齐次线性方程组 $\begin{equation}\left\{\begin{aligned}&x_{1}+x_{2}-x_{4}=0\\&2x_{1}+x_{2}+2x_{3}-2x_{4}=0\\&3x_{1}+2x_{2}+2x_{3}-3x_{4}=0\end{aligned}\right.\end{equation}$，其解法如下：

     1.   写出系数矩阵 $A=\begin{pmatrix}1&1&0&-1\\2&1&2&-2\\3&2&2&-3\end{pmatrix}$；

     2.   将 $A$ 通过初等行变换转为行最简形（过程略，自行尝试），$\begin{pmatrix}1&0&2&-1\\0&1&-2&0\\0&0&0&0\end{pmatrix}$；

     3.   行最简形转为方程组：$\begin{equation}\left\{\begin{aligned}&x_{1}+2x_{3}-x_{4}=0\\&x_{2}-2x_{3}=0\end{aligned}\right.\end{equation}$，用 $x_{3}$、$x_{4}$ 表示 $x_{1}$、$x_{2}$ 得 $\begin{equation}\left\{\begin{aligned}&x_{1}=-2x_{3}+x_{4}\\&x_{2}=2x_{3}+0x_{4}\end{aligned}\right.\end{equation}$；

     4.   假设与通解：令 $x_{3}=k_{1}$，$x_{4}=k_{2}$，

          则通解表示为 $\begin{pmatrix}x_{1}\\x_{2}\\x_{3}\\x_{4}\end{pmatrix}=k_{1}\begin{pmatrix}-2\\2\\1\\0\end{pmatrix}+k_{2}\begin{pmatrix}1\\0\\0\\1\end{pmatrix}$，也可以理解为式子中含有几个 $x_{3}$、$x_{4}$

          基础解系（也即最终目标）为：$(-2, 2, 1, 0)^{T}$、$(1, 0, 0, 1)^{T}$

4.   解非齐次线性方程组

     一个多元非齐次线性方程组 $\begin{equation}\left\{\begin{aligned}&x_{1}+x_{2}-x_{4}=2\\&2x_{1}+x_{2}+2x_{3}-2x_{4}=5\\&3x_{1}+2x_{2}+2x_{3}-3x_{4}=7\end{aligned}\right.\end{equation}$，其解法如下：

     1.   先求出增广矩阵 $(A, B)=\begin{pmatrix}1&1&0&-1&2\\2&1&2&-2&5\\3&2&2&-3&7\end{pmatrix}$；

     2.   化成行最简形：$\begin{pmatrix}1&0&2&-1&3\\0&1&-2&0&-1\\0&0&0&0&0\end{pmatrix}$；

     3.   求通解与基础解系；

          由行最简形可得 $\begin{equation}\left\{\begin{aligned}&x_{1}+2x_{3}-x_{4}=3\\&x_{2}-2x_{3}=-1\end{aligned}\right.\end{equation}$，用 $x_{3}$、$x_{4}$ 表示 $x_{1}$、$x_{2}$ 得 $\begin{equation}\left\{\begin{aligned}&x_{1}=-2x_{3}+x_{4}+3\\&x_{2}=2x_{3}+0x_{4}-1\end{aligned}\right.\end{equation}$；

          有 $\forall k_{1},k_{2}$，使得 $x_{3}=k_{1}$、$x_{4}=k_{2}$，

          得出最终结果：$\begin{pmatrix}x_{1}\\x_{2}\\x_{3}\\x_{4}\end{pmatrix}=k_{1}\begin{pmatrix}-2\\2\\1\\0\end{pmatrix}+k_{2}\begin{pmatrix}1\\0\\0\\1\end{pmatrix}+\begin{pmatrix}3\\-1\\0\\0\end{pmatrix}$；

          其中，通解为 $k_{1}\begin{pmatrix}-2\\2\\1\\0\end{pmatrix}+k_{2}\begin{pmatrix}1\\0\\0\\1\end{pmatrix}$，该非齐次线性方程组的一个解为 $(3, -1, 0, 0)^{T}$；

## 例题

1.   将行列式转换成上三角行列式再计算，$\begin{vmatrix}3&1&4&-2\\2&5&3&1\\1&2&2&-1\\-1&4&-3&5\end{vmatrix}=\underline{\hspace{3em}}$
2.   主对角线相同，其他元素是另一个相同的数；思路是将其他行都累加到第 $1$ 行，再提公因式使第 $1$ 行全为 $1$，$\begin{vmatrix}5&2&2&2\\2&5&2&2\\2&2&5&2\\2&2&2&5\end{vmatrix}=\underline{\hspace{3em}}$
3.   利用单位矩阵组成联合矩阵形式，再进行初等行变换；$A=\begin{pmatrix}1&2&-4\\2&3&-7\\-1&-1&2\end{pmatrix}$，求 $A^{-1}$
4.   利用等式两边同时左乘 $A^{-1}$ 来消 $A$；$A=\begin{pmatrix}1&2&-4\\2&3&-7\\-1&-1&2\end{pmatrix}$，$B=\begin{pmatrix}1&0\\0&-1\\1&2\end{pmatrix}$，若 $AX=B$，求矩阵 $X$
5.   合理运用相关矩阵公式，其中 $A^{*}=|A|A^{-1}$；$A$ 为 $3$ 阶矩阵，$|A|=\frac{1}{2}$，求 $|(2A)^{-1}-5A^{*}|$
6.   分块矩阵的计算；$\begin{vmatrix}1&2&0&0\\3&4&0&0\\0&0&5&6\\0&0&7&8\end{vmatrix}=\underline{\hspace{3em}}$；$\begin{pmatrix}0&1&0&0\\0&0&2&0\\0&0&0&3\\4&0&0&0\end{pmatrix}^{-1}=\underline{\hspace{3em}}$
7.   有 $\alpha_{1}=(1,2,3)^{T}$，$\alpha_{2}=(1,1,2)^{T}$，$\alpha_{3}=(0,2,2)^{T}$，$\alpha_{4}=(-1,-2,-3)^{T}$，$\beta=(2,5,7)^{T}$，求 $\beta$ 由 $\alpha_{1}$、$\alpha_{2}$、$\alpha_{3}$ 以及 $\alpha_{4}$ 线性表示的表达式
8.   求  $\alpha_{1}=(1,-1,-2,1)^{T}$，$\alpha_{2}=(1,1,0,-1)^{T}$，$\alpha_{3}=(2,-1,-3,0)^{T}$，$\alpha_{4}=(2,3,1,-2)^{T}$，$\alpha_{5}=(1,-2,-3,1)^{T}$ 的秩以及一个最大无关组，并将其余向量用该最大无关组线性表示
9.   求 $A=\begin{pmatrix}1&1&2&2&1\\-1&1&-1&3&-2\\-2&0&-3&1&-3\\1&-1&0&-2&1\end{pmatrix}$ 的秩以及一个最高阶非 $0$ 子式；注意是在原来 $A$ 中取最高阶非 $0$ 子式，且要保证 $|D_{r}|\neq0$
10.   方程组 $\begin{equation}\left\{\begin{aligned}&x_{1}+ax_{2}=0\\&x_{2}+ax_{3}=0\\&x_{3}+ax_{4}=0\\&x_{1}+x_{4}=0\end{aligned}\right.\end{equation}$ 有非 $0$ 解，求 $a$；将方程转为行列式 $|A|$，有非 $0$ 解，表示 $|A|=0$
11.   已知 $\alpha_{1}=(1,0,0,1)^{T}$，$\alpha_{2}=(a,1,0,0)^{T}$，$\alpha_{3}=(0,a,1,0)^{T}$，$\alpha_{4}=(0,0,a,1)^{T}$ 成线性相关，求 $a$；同第 10 题，不同问法
12.   $(1,3,0)^{T}$ 不能由 $(1,2,1)^{T}$、$(2,3,a)^{T}$、$(1,a+2,-2)^{T}$ 线性表示，求 $a$

## 脚手架

1.   $\begin{vmatrix}1&2\\3&4\end{vmatrix}$
2.   $\begin{pmatrix}1&2\\3&4\end{pmatrix}$
3.   $=\underline{\hspace{3em}}$
4.   $\Leftrightarrow$
