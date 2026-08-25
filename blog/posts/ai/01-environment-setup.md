---
title: "ai | 01_artificial_intelligence_dev_env_configuration"
description: "dev environment for Artificial Intelligence."
date: "2023-04-08T03:52:00.000Z"
updated: "2024-12-12T08:23:57.000Z"
tags: []
draft: false
layout: "post"
slug: "environment-setup"
---

## dev | artificial-intelligence-dev-env-configuration

>   一些在接触 Artificial Intelligence 过程中的各类问题集合

## anaconda

以下操作都默认在 **Anaconda Prompt (Anaconda)** 中进行

### cmd

1.   创建虚拟环境：`conda create -n 01_stable_diffusion_stable_diffusion_webui python=3.10.6`
2.   列出 jupyter 内核列表：`jupyter kernelspec list`
3.   连接 jupyter 内核和虚拟环境：`python -m ipykernel install --prefix=F:\artificial-intelligence\anaconda --name=01_stable_diffusion_stable_diffusion_Webui`
4.   移除已连接的 kernel：`jupyter kernelspec remove 内核名`
5.   列出所有虚拟环境：`conda env list`
6.   启用环境：`conda activate 环境名`
7.   退出虚拟环境：`conda deactivate`
8.   创建环境，名为 "环境名" 的 python3.9 基础环境：`conda create -n 环境名 python=3.9`
9.   删除环境：`conda remove -n 环境名 --all`
10.   虚拟环境改名，通过 clone 的方式改名：`conda create -n 新名字 --clone 旧环境名字`，`conda remove -n 旧环境名字 --all`
11.   列出当前环境下的所有库：`conda list`
12.   安装库，安装 NumPy 库，并指定版本 1.12.5：`pip install numpy==1.21.5 -i https://pypi.tuna.tsinghua.edu.cn/simple`
13.   requirements.txt 文件安装：`pip install -r requirements.txt`，`conda install --file requirements.txt`
14.   查看当前环境下某个库的版本：`pip show numpy`

### environment config

采用 Anaconda + Jupyter 来管理全局环境，个人环境目录如下：

```bash
F:/Artificial-Intelligence/
    ├── Anaconda								# Anaconda 安装目录
    ├── Notebooks								# 存放 .ipynb 笔记本
    │   ├── 01_stable_diffusion_stable_diffusion_Webui.ipynb
    │   ├── 02_vits.ipynb
    │   └── 03_gpt_chatglm.ipynb
    ├── References								# 整个项目所需要的一些知识内容，教程等
    ├── Projects								# 所有 ai 项目
    │   ├── 00_models							# 存放所有大模型文件
    │   │   └── 01_stable_diffusion_models		# 项目模型
    │   ├── 01_stable_diffusion					# 项目分类，使用 01.xxx 来排序
    │   ├── 02_vits
    │   └── 03_gpt
    │       ├── chatglm							# 子项目
    │       └── nanogpt
    ├── README.md								# 本文件
    └── Scripts									# 一些脚本，例如自动部署，配置环境等
```

1.   安装

     1.   获取 [Anaconda](https://www.anaconda.com/) 安装文件，直接获取到对应的系统版本即可，如果打不开官网，选择 [备用镜像站](https://repo.anaconda.com/archive/)
     2.   安装过程中，可选项选择：**Just me**，**选择一个磁盘空间相对大的盘（下面以 F 盘为例）**，**最后一个勾选选项 Advanced Options 中，把 `Add Anaconda3 ...` 前的框给去掉**

2.   配置环境变量：在系统中检查环境变量是否配置正确，以 Windows 为例，在控制面板中打开 **编辑系统环境变量**，选择 **环境变量**、**下方的系统变量**、**找到名为 Path 的项双击打开（或者点击编辑）**，选择 **新建**，并填入以下配置：

     ```bash
     # 需要根据具体情况修改配置，参考上文环境变量配置
     F:\Artificial-Intelligence\Anaconda
     F:\Artificial-Intelligence\Anaconda\Scripts
     F:\Artificial-Intelligence\Anaconda\Library\bin
     ```

3.   更换软件源：输入：`conda config --set show_channel_urls yes` 后，会在 `%USERPROFILE%\用户名\` 生成一个 `.condarc` 文，打开这个文件，填入以下内容：

     ```ini
     channels:
       - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
       - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
       - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
     ssl_verify: true
     ```

     至此，Anaconda 基本环境安装完成

4.   （可选）在 terminal 中配置 Anaconda 环境

     1.   在 terminal 中右边三角打开 **设置**；在设置界面中，打开左下角的 **打开 JSON 文件**

     2.   找到 34 行附近的 `profiles` 项，在 `profiles.list` 中添加如下配置：

          ```json
          {
              "commandline": "%windir%\\System32\\cmd.exe /K F:\\Artificial-Intelligence\\Anaconda\\Scripts\\activate.bat",
              "guid": "{xxxx} 在 管理员模式下的 cmd 中输入 new-guid",
              "hidden": false,
              "name": "Anaconda"
          }
          ```

5.   Jupyter

     1.   找到 Jupyter：安装完成 **Anaconda** 后，其默认自带了 **Jupyter Notebook**，在 **开始菜单** 中可以找到 
          1.   **Jupyter Notebook (Anaconda)**：后续基本所有的 ai 项目都要从 Jupyter 启动，管理，修改
          2.   **Anaconda Prompt (Anaconda)**：Anaconda 默认的控制台，但是在添加了环境变量后，也可以在 terminal 中使用 `conda` 指令来调用 Anaconda
          3.   点击 **Jupyter Notebook (Anaconda)** 后，会出现 **内核命令提示符**，随后弹出浏览器界面，这就是启动成功了
     2.   修改 Jupyter 的默认工作路径。**在初次打开 Jupyter 后**，其显示的文件目录是默认的 `%USERPROFILE%\用户名`，并不符合我们 ai 项目的实际工作路径，因此需要将默认工作路径给修改掉，这里选择 `F:\Artificial-Intelligence\Notebooks` 作为默认的工作目录
          1.   打开 **Anaconda Prompt (Anaconda)**，输入：`jupyter notebook --generate-config`，此时会回显一个地址 `%USERPROFILE%\用户名\.jupyter\jupyter_notebook_config.py`
          2.   使用各种文本编辑器，修改 `%USERPROFILE%\用户名\.jupyter\jupyter_notebook_config.py` 的内容，找到 `# c.NotebookApp.notebook_dir` 项，将其修改为（即去掉 # 号）：`c.NotebookApp.notebook_dir = 'F:\Artificial-Intelligence\Notebooks'`，按照具体情况修改，保存关闭
          3.   在开始菜单找到 **Jupyter Notebook (Anaconda)** 快捷方式，右键、更多、打开文件位置，然后对着快捷方式右键、属性，将 **目标** 一栏中最后的 `"%USERPROFILE%/` 给删掉，保存
          4.   修改完成后，再打开 **Jupyter Notebook (Anaconda)** 即可发现成功修改好了默认工作目录
          5.   （可选）修改 **Jupyter Notebook** 默认字体，打开文件 `F:\Artificial-Intelligence\Anaconda\Lib\site-packages\nbclassic\static\components\codemirror\lib\codemirror.css`，找到 `font-family: monospace;` 修改成（末尾分号要保留） `font-family: 'Fira Code Light','Consolas';`，保存
          6.   （应急），如果发现无法启动 **Jupyter Notebooks (Anaconda)** 了，输入以下指令来重装 juypyter：`conda uninstall pyzmq`，`conda install pyzmq`，`conda install jupyter`
     3.   连接虚拟环境。Jupyter 内核 默认只与 base 环境连接，只有内核与虚拟环境连接后，才能方便后续 ai 操作（能够在 jupyter notebooks 中直接选择虚拟环境，并进行相关操作），现在给出一个连接其他内核的示例，以下操作都在 **Anaconda Prompt (Anaconda)** 中执行
          1.   列出 jupyter 当前内核：`jupyter kernelspec list`
          2.   **初次使用**，安装 ipykernel，在 base 环境下：`pip install ipykernel`
          3.   导入虚拟环境到 Jupyter 的 kernel 中：`python -m ipykernel install --user --name=虚拟环境名`，或者指定安装目录：`python -m ipykernel install --name=虚拟环境名 --prefix=F:\Artificial-Intelligence\Anaconda`
          4.   删除虚拟环境的 kernel 内核：`jupyter kernelspec remove 虚拟环境名`

## PyTorch

深度学习常用框架，不同的 project 会使用不同的 pytorch 版本，需要具体情况分析

1.   使用 `nvidia-smi` 指令查看当前机器所支持的 **CUDA Version**，本机使用的是 **RTX 2060 + CUDA 11.7** 版本。
2.   以项目 **stable-diffusion-webui** 为例，其项目中的 `requirements_versions.txt` 中指定了 `torch=1.12.1`，故我们需要找到对应的版本，在 [网上搜索](https://pytorch.org/get-started/previous-versions/) `torch=1.12.1` 对应的 cuda 版本，得到 10.2、11.3 以及 11.6
3.   选择合适自己 CUDA 版本的指令，在 **Anaconda Prompt** 中先启用对应的虚拟环境：`conda activate stable-diffusion-webui`，然后输入所给的指令：`conda install pytorch==1.12.1 torchvision==0.13.1 torchaudio==0.12.1 cudatoolkit=11.6 -c pytorch -c conda-forge`，之后即可各 project 环境隔离使用

## references

1.   [如何在 Windows Terminal 中启用 Anaconda 命令](https://www.jianshu.com/p/ab1315000cd9)
2.   [Python深度学习：安装Anaconda与PyTorch库（GPU版本）](https://www.bilibili.com/video/BV1cD4y1H7Tk)
