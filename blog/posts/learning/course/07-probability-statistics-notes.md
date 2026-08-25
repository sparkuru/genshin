---
title: "probability-and-statistics"
description: "概率论与数理统计，301 大纲要求。"
date: "2023-12-04T07:39:00.000Z"
updated: "2024-08-20T02:41:01.000Z"
tags: []
draft: false
layout: "post"
slug: "probability-statistics-notes"
---

## probability-and-statistics

>   概率论与数理统计速记手册

## 速记

| 检验量       | 条件          | 检验统计量 | $H_{0}$ | $H_{1}$ | 拒绝域 | 置信区间 |
| ------------ | ------------- | ---------- | ------- | ------- | ------ | -------- |
| $\mu$        | $\sigma$ 已知 |            |         |         |        |          |
| .            |               |            |         |         |        |          |
| .            |               |            |         |         |        |          |
| $\mu$        | $\sigma$ 未知 |            |         |         |        |          |
| .            |               |            |         |         |        |          |
| .            |               |            |         |         |        |          |
| $\sigma^{2}$ | $\mu$ 未知    |            |         |         |        |          |
| .            |               |            |         |         |        |          |
| .            |               |            |         |         |        |          |

## 公式

1.   $A_{m}^{n}=\frac{m!}{(m-n)!}$，$C_{m}^{n}=\frac{A_{m}^{n}}{A_{n}^{n}}=\frac{m!}{(m-n)!n!}$

2.   随机事件和概率

     1.   $p(A\cup{B})=p(A)+p(B)-p(A\cap{B})$
     2.   $p(A-B)=p(A)-p(AB)=p(A\bar{B})$
     3.   条件概率公式：$p(AB)=p(A|B)p(B)=p(B|A)p(A)$
     4.   若 $\begin{equation}\left\{\begin{aligned}&p(A|B)=p(A)\\&p(B|A)=p(B)\end{aligned}\right.\end{equation}$，则 $p(AB)=p(A)p(B)$，$A$、$B$ 独立
     5.   全概率公式，$p(A)=p(A|B_{1})p(B_{1})+p(A|B_{2})p(B_{2})+p(A|B_{3})p(B_{3})$
     6.   贝叶斯公式，$p(B_{2}|A)=\frac{p(AB_{2})}{p(A)}=\frac{p(A|B_{2})p(B_{2})}{p(A|B_{1})p(B_{1})+p(A|B_{2})p(B_{2})+p(A|B_{3})p(B_{3})}$

3.   随机变量的独立性：若离散型随机变量 $X$、$Y$ 独立，则关于 $X$ 与 $Y$ 的联合分布律各行（列）成比例

4.   期望、方差、协方差

     1.   期望；离散型，$EX=\Sigma_{i=1}^{+\infty}X_{i}\cdot{P\{X=x_{i}}\}$；连续型，$EX=\int_{-\infty}^{+\infty}x\cdot{f(x)}dx$

     2.   方差：$DX=E(X^{2})-(EX)^{2}$

     3.   期望与方差的性质

          | 期望                                    | 方差                                   |
          | --------------------------------------- | -------------------------------------- |
          | $E(c)=c$                                | $D(c)=0$                               |
          | $E(cX)=cEX$                             | $D(cX)=c^{2}DX$                        |
          | $E(X\pm{Y})=EX\pm{EY}$                  | $D(X\pm{Y})=DX+DY$，要求 $X$、$Y$ 独立 |
          | $E(XY)=EX\cdot{EY}$，要求 $X$、$Y$ 独立 |                                        |

     4.   协方差（Covariance）；

          1.   $Cov(X,Y)=E(XY)-EX\cdot{EY}$；
          2.   $D(X\pm{Y})=DX+DY\pm{2Cov(X,Y)}$，显然当 $X$、$Y$ 独立时，$D(X\pm{Y})=DX+DY$

     5.   相关系数；

          1.   $\rho_{XY}=\frac{Cov(X,Y)}{\sqrt{DX}\sqrt{DY}}$
          2.   若 $\rho_{XY}=0$，则称 $X$、$Y$ 不相关

5.   常用分布

     | 分布       | 表示法                     | 分布律或概率密度                                             | 数学期望            | 方差                                           |
     | ---------- | -------------------------- | ------------------------------------------------------------ | ------------------- | ---------------------------------------------- |
     | 0 - 1 分布 |                            | $P\{X=k\}=p^{k}(1-p)^{1-k}$，$k=0,1$                         | $p$                 | $p(1-p)$                                       |
     | 二项分布   | $X\sim{B(n,p)}$            | $P\{X=k\}=C_{n}^{k}p^{k}(1-p)^{1-k}$，$k=0,1,2,...,n$        | $np$                | $np(1-p)$                                      |
     | 泊松分布   | $X\sim{P(\lambda)}$        | $P\{X=k\}=\frac{\lambda^{k}e^{-\lambda}}{k!}$，$k=0,1,2,...$ | $\lambda$           | $\lambda$                                      |
     | 几何分布   | $X\sim{G(p)}$              | $P\{X=k\}=(1-p)^{k-1}p$，$k=1,2,...$                         | $\frac{1}{p}$       | $\frac{1-p}{p^{2}}$                            |
     | 超几何分布 |                            | $P\{X=k\}=\frac{C_{M}^{k}C_{N-M}^{n-k}}{C_{N}^{n}}$          | $\frac{nM}{N}$      | $\frac{nM}{N}(1-\frac{M}{N})(\frac{N-n}{N-1})$ |
     | 均匀分布   | $X\sim{U(a,b)}$            | $f(x)=\begin{equation}\left\{\begin{aligned}&\frac{1}{b-a}, &a&lt;x&lt;b\\&amp;0,&amp;others\end{aligned}\right.\end{equation}$ | $\frac{a+b}{2}$     | $\frac{(b-a)^2}{12}$                           |
     | 指数分布   | $X\sim{E(\lambda)}$        | $f(x)=\begin{equation}\left\{\begin{aligned}&amp;\lambda{e^{-\lambda{x}}}, &amp;x&gt;0\\&0,&x\leq0\end{aligned}\right.\end{equation}$ | $\frac{1}{\lambda}$ | $\frac{1}{\lambda^{2}}$                        |
     | 正态分布   | $X\sim{N(\mu,\sigma^{2})}$ | $f(x)=\frac{1}{\sqrt{2\pi}\sigma}e^{-\frac{(x-\mu)^{2}}{2\sigma^{2}}}$，$-\infty&lt;x&lt;+\infty$ | $\mu$               | $\sigma^{2}$                                   |

6.   正态分布

     $X\sim{N(\mu,\sigma^{2})}\Rightarrow{\frac{X-\mu}{\sigma}\sim{N(0,1)}}$，$P\{\frac{X-\mu}{\sigma}\leq{\frac{b-\mu}{\sigma}}\}=\Phi(\frac{b-\mu}{\sigma})$，关键在于 $\leq$ 后的值
     $$
     \begin{align}
     P\{a&lt;X&lt;b\}
     	&amp;=P\{X\leq{b}\}-P\{X\leq{a}\} \\
     	&amp;=P\{\frac{X-\mu}{\sigma}\leq{\frac{b-\mu}{\sigma}}\}-P\{\frac{X-\mu}{\sigma}\leq{\frac{a-\mu}{\sigma}}\} \\
     	&amp;=\Phi(\frac{b-\mu}{\sigma})-\Phi(\frac{a-\mu}{\sigma})
     \end{align}
     $$
     即将一个正态分布转换成标准正态分布，再用标准正态分布函数 $\Phi(X)$ 查表的方式解决问题

     关于标准正态概率密度函数图形 $\Phi(X)$ 一些性质如下

     1.   横轴是 $X$，纵轴是 $\phi(X)$，图像关于 $X=0$ 对称
     2.   $\Phi(-X)=1-\Phi(X)$
     3.   $\Phi(0)=\frac{1}{2}$
     4.   若 $X\sim{N(\mu_{1},\sigma_{1}^{2})}$、$Y\sim{N(\mu_{2},\sigma_{2}^{2})}$，且 $X$、$Y$ 独立，则有 $aX\pm{bY}\sim{N(a\mu_{1}\pm{b\mu_{2}},a^{2}\mu_{1}^{2}\pm{b^{2}\mu_{2}^{2}})}$

7.   大数定律、中心极限定理（转化为正态分布）、切比雪夫不等式

     1.   大数定律；当 $n$ 充分大时，$\bar{X}=\frac{1}{n}\Sigma_{i=1}^{n}X_{i}$ 很可能接近于 $E(\bar{X})=\frac{1}{n}\Sigma_{i=1}^{n}E(X_{i})$
     2.   中心极限定理；在 $X_{1},X_{2},...,X_{n},...$ 独立同分布的情况下，当 $n$ 充分大时，$\Sigma_{i=1}^{n}X_{i}$ 的值近似于 $N(nE(X_{i}),nD(X_{i}))$，也即期望和方差的 $n$ 倍；特别的，若 $Y\sim{B(n,p)}$，则当 $n$ 充分大时，$Y$ 的值近似于 $N(np,np(1-p))$
     3.   切比雪夫不等式

8.   抽样分布

     1.   若 $x_{1}^{2},x_{2}^{2},...,x_{n}^{2}$ 独立且均服从 $N(0,1)$，则服从卡方分布：$x_{1}^{2}+x_{2}^{2}+...+x_{n}^{2}\sim{\chi^{2}(n)}$
     2.   若 $X\sim{N(0,1)}$，$Y\sim{\chi^{2}(n)}$，且 $X$、$Y$ 独立，则有 $t$ 分布：$\frac{X}{\sqrt{Y/n}}\sim{t(n)}$
     3.   若 $U\sim{\chi^{2}(n_{1})}$，$V\sim{\chi^{2}(n_{2})}$，且 $U$、$V$ 独立，则有 $F$ 分布：$\frac{U/n_{1}}{V/n_{2}}\sim{F(n_{1},n_{2})}$

9.   矩估计与最大似然估计

     1.   矩估计：计算 $EX=\bar{X}$，这是一个含 $\theta$ 的结果，化简得出 $\theta$ 值即为矩估计值 $\hat{\theta}$
     2.   最大似然估计：计算 $\begin{equation}\left\{\begin{aligned}&amp;L(\theta)=\prod_{i=1}^{n}P\{X=x_{i};\theta\}, &amp;离散\\&amp;L(\theta)=\prod_{i=1}^{n}f(x_{i};\theta),&amp;连续\end{aligned}\right.\end{equation}$，一般需要取对数运算

10.   置信区间

      根据题目要求待估计什么参数，已知什么参数来选择，一般都是给正态分布区间 $N(\mu,\sigma^{2})$，置信度例 $0.95=1-\alpha$，则 $\frac{\alpha}{2}=0.025$

     | 待估参数     | 其他参数          | 置信区间                                                     |
     | ------------ | ----------------- | ------------------------------------------------------------ |
     | $\mu$        | $\sigma^{2}$ 已知 | $(\bar{X}-\frac{\sigma}{\sqrt{n}}z_{\frac{\alpha}{2}},\bar{X}+\frac{\sigma}{\sqrt{n}}z_{\frac{\alpha}{2}})$ |
     | $\mu$        | $\sigma^{2}$ 未知 | $(\bar{X}-\frac{S}{\sqrt{n}}t_{\frac{\alpha}{2}}(n-1),\bar{X}+\frac{S}{\sqrt{n}}t_{\frac{\alpha}{2}}(n-1))$，其中 $S$ 是标准差 |
     | $\sigma^{2}$ | $\mu$ 未知        | $(\frac{(n-1)S^{2}}{\chi_{\frac{\alpha}{2}}^{2}(n-1)},\frac{(n-1)S^{2}}{\chi_{1-\frac{\alpha}{2}}^{2}(n-1)})$ |

11.   假设检验

      1.   假设检验表

           | 检验参数     | 其他参数          | 检验统计量                                   | $H_{0}$                        | $H_{1}$                        | 拒绝域                                                       |
           | ------------ | ----------------- | -------------------------------------------- | ------------------------------ | ------------------------------ | ------------------------------------------------------------ |
           | $\mu$        | $\sigma^{2}$ 已知 | $U=\frac{\bar{X}-\mu_{0}}{\sigma/\sqrt{n}}$  | $\mu\leq\mu_{0}$               | $\mu&gt;\mu_{0}$                  | $u\geq{u_{\alpha}}$                                          |
           |              |                   |                                              | $\mu\geq\mu_{0}$               | $\mu<\mu_{0}$                  | $u\leq{-u_{\alpha}}$                                         |
           |              |                   |                                              | $\mu=\mu_{0}$                  | $\mu\neq\mu_{0}$               | $\lvert{u}\rvert>u_{\frac{\alpha}{2}}$                       |
           |              | $\sigma^{2}$ 未知 | $U=\frac{\bar{X}-\mu_{0}}{S/\sqrt{n}}$       | $\mu\leq\mu_{0}$               | $\mu>\mu_{0}$                  | $t\geq{t_{\alpha}(n-1)}$                                     |
           |              |                   |                                              | $\mu\geq\mu_{0}$               | $\mu<\mu_{0}$                  | $t\leq{-t_{\alpha}(n-1)}$                                    |
           |              |                   |                                              | $\mu=\mu_{0}$                  | $\mu\neq\mu_{0}$               | $\lvert{t}\rvert>t_{\frac{\alpha}{2}}(n-1)$                  |
           | $\sigma^{2}$ | $\mu$ 未知        | $\chi^{2}=\frac{(n-1)S^{2}}{\sigma_{0}^{2}}$ | $\sigma^{2}\leq\sigma_{0}^{2}$ | $\sigma^{2}>\sigma_{0}^{2}$    | $\chi^{2}\geq\chi_{\alpha}^{2}(n-1)$                         |
           |              |                   |                                              | $\sigma^{2}\geq\sigma_{0}^{2}$ | $\sigma^{2}<\sigma_{0}^{2}$    | $\chi^{2}\leq\chi_{1-\alpha}^{2}(n-1)$                       |
           |              |                   |                                              | $\sigma^{2}=\sigma_{0}^{2}$    | $\sigma^{2}\neq\sigma_{0}^{2}$ | $\chi^{2}\geq\chi_{\frac{\alpha}{2}}^{2}(n-1)$ 或 $\chi^{2}\leq\chi_{1-\frac{\alpha}{2}}^{2}(n-1)$ |

      2.   两类错误；第一类错误：$H_{0}$ 为真，但拒绝 $H_{0}$；第二类错误：$H_{0}$ 为假，但接受 $H_{0}$；

## 例题

1.   设 $p(A\cup{B})=0.8$，$p(B)=0.4$，求 $p(A|\bar{B})$；...... $\frac{2}{3}$
2.   条件概率例题；
     1.   甲、乙独立地对同一目标射击一次，命中概率分别为 $0.6$、$0.5$，求至少一人射中的概率；...... $0.8$
     2.   甲、乙独立地对同一目标射击一次，命中概率分别为 $0.6$、$0.5$，现已知目标被命中，求是被甲射中的概率；...... $0.75$
     3.   甲、乙任选一人对同一目标射击一次，命中概率分别为 $0.6$、$0.5$，求目标被甲射中的概率；...... $0.3$
     4.   甲、乙任选一人对同一目标射击一次，命中概率分别为 $0.6$、$0.5$，现已知目标被命中，求是被甲射中的概率；...... $\frac{6}{11}$
3.   标准正态分布例题；设 $X\sim{N(2,1)}$，$Y\sim{N(1,4)}$，且 $X$、$Y$ 独立，求 $P\{2X-Y>3\}$；...... $\frac{1}{2}$
4.   中心极限定理；设 $Y\sim{B(100,0.2)}$，若 $Y$ 不大于 $a$ 的概率不小于 $\Phi(2)=0.977$，求 $a$；...... $28$
5.   抽样分布；若有 $X\sim{t(n)}$，$n>1$，$Y=\frac{1}{x^{2}}$，则 $Y$ 是什么分布；...... $Y\sim{F(n,1)}$
6.   矩估计与最大似然估计；设 $X$ 的概率密度为 $f(x;\theta)=\begin{equation}\left\{\begin{aligned}&\theta{x^{-(\theta+1)}}, &x>1\\&0,&x\leq1\end{aligned}\right.\end{equation}$，$\theta>1$，其中 $X_{1},X_{2},...,X_{n}$ 为来自总体 $X$  的样本，求 $\theta$ 的矩估计量和最大似然估计量；...... 矩估计量 $\hat{\theta}=\frac{\bar{X}}{\bar{X}-1}$，取对数得 $\ln{L(\theta)}=n\ln{\theta}-(\theta+1)\cdot\Sigma_{i=1}^{n}\ln{X_{i}}$，对 $\theta$ 求导取零点得最大似然估计量 $\hat{\theta}=\frac{n}{\Sigma_{i=1}^{n}\ln{X_{i}}}$
7.   置信区间；$x_{1},x_{2},...,x_{n}$ 为来自总体 $N(\mu,\sigma^{2})$ 的样本，$\bar{x}=9.5$，$\mu$ 的置信度为 $0.95$ 的双侧置信区间的置信上限为 $10.8$，求 $\mu$ 的置信度为 $0.95$ 的双侧置信区间；...... $\mu$ 和 $\sigma^{2}$ 都未知，则置信区间为 $(\bar{X}-\frac{S}{\sqrt{n}}t_{\frac{\alpha}{2}}(n-1),\bar{X}+\frac{S}{\sqrt{n}}t_{\frac{\alpha}{2}}(n-1))=$，其中 $\bar{X}=9.5$、$\frac{S}{\sqrt{n}}t_{\frac{\alpha}{2}}(n-1)=10.8$，则可得置信区间为 $(8.2,10.8)$

## 脚手架

1.   $\cap$
2.   $\cup$
3.   $\bar{A}$
4.   $=\underline{\hspace{3em}}$
5.   $\begin{equation}\left\{\begin{aligned}&A=0\\&B=0,\\\end{aligned}\right.\end{equation}$
6.
