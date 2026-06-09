```bash
git config --global user.email i@majo.im
git config --global user.name wkyuu
git config --global credential.helper store
git config --global init.defaultbranch main
git config --global core.editor vim
git config --global core.autocrlf input
git config --global core.quotepath false
git config --global pull.rebase true

git config --global --list
```

## init

### 项目全新初始化

*注：github 上新增的 repository 默认 branch 名称都是 main 了，但是本地* *`git init`* *时还是 main，可以用* *`git branch -m main main`* *来改变本地默认 branch 的名称，也可以修改全局默认设置* *`git config --global init.defaultBranch main`*

- 远程

  1. 在 github 上新建一个 repository，得到该 repo 的地址（举个例子）为 `https://github.com/username/remote.git`
  2. 选择创建 `.gitignore` 模板文件，也可以选择 `License`，除非有很明确的版权声明，否则一律建议使用 MIT 或 GPL3
- 本地

  1. 创建项目初始化文件夹 `mkdir project`
  2. 在 `project` 文件夹中，初始化 `.git` 文件夹用于监控整个项目：`git init`
  3. 在本地创建一些文件，这里以 `README.md` 为例，并写入项目基本介绍（不写也行）
  4. 为 `README.md` 添加 commit：`git add README.md`，然后 `git commit -m "init"`
  5. （可选）修改 branch 的名称：`git branch -M main`；修改这个的原因是，一般新创建的 remote 仓库会自动将主 branch 命名为 main，而想要在 main 上写代码就必须同步 main 这个名称，当然也可以把远程的改成 master
  6. 绑定远程仓库：`git remote add origin https://github.com/username/remote.git`。这条指令的意思为为远程仓库 `remote.git` 添加一个别名 `origin`，今后推送的时候直接输入 `origin` 即可，而不是一长串 url，同时还可以用 `origin/main` 来标识远程的 main branch；当然也可以修改成其他的，反正远程对于本地来说就叫 `origin`；可以使用 `git remote -v` 查看具体的 remote 信息
  7. 然后执行第一次 push：`git push origin main`，有几个问题

      1. 如果没有配置过默认登录用户，则这里一般会有一个验证登录的选项，按流程登录就行
      2. 如果在远程新建仓库时，勾选了 `.gitignore`、`license`、`readme` 等内容，导致 push 被拒绝，这是因为本地 repo 和远程 repo 有独立的 commit，简单来讲就是没有完全同步，此时的做法是先 `git pull --rebase origin main`，这条指令可以自动根据本仓库所有文件添加顺序对 commit 进行排序、自动整合，然后再 `git push origin main`
      3. 设置 `git push -u origin main`，即设置默认 up-stream，之后直接输入 `git push` 就默认 push 到 `origin` 了

### 远程已有项目，在本地初始化

在 github 已经有一个属于自己的仓库，想在一个新的文件夹空间再拉一个 branch 来协同操作 *（或者想要把新文件夹当作 main branch，一般用于换一台电脑的情况）* 。

- 远程

  记录远程已有仓库：`https://github.com/username/remote.git`
- 本地

  1. 在新的文件夹下同样先初始化：`git init`
  2. 执行 `git add .` 和 `git commit -m "xxx"`，这样会创建第一个 commit
  3. 绑定仓库：`git remote add origin main https://github.com/username/remote.git`
  4. 绑定远程仓库的 `origin/main` 分支到本地主分支：`git branch --set-upstream-to=origin/main main`
  5. 拉取一次远程分支：`git pull`
  6. 正常提交：`git push`

## push

**以一次正常代码提交为例**

1. 本地完成了一些代码的编写，在项目文件夹内执行 `git status`，可以查看到有哪些文件被修改了
2. 选择想要 push 的文件 *test1*，*test2*，执行 `git add test1 test2`，这里也可以直接 `git add *`，后者这种方式更常用一些
3. 为选择的文件添加一个版本 commit：`git commit -m "say sth"`
4. 将文件 push 出去即可：`git push`

### 重新修改 git 暂存区状态

就是想重新添加文件

1. 删除暂存区内容：`git rm -r --cached filename`，这里可以把 *filename* 改成  *.*  以此来清空暂存区
2. 重新 `git add filename` 即可

### 对当前 add 过的内容不满意，想要重新提交

`git reset`，即可重置上一次 add 的状态；如果 add 且 commit 了，但是又想回复成 add 后、commit 前的状态，则 `git reset HEAD~1` 即可

### .gitignore 文件

```ini
# 注释
文件夹	# 单个文件夹目录
*.txt	# 所有 txt 文件
各类通配符
```

### 同时 push 到多个仓库

`git remote set-url --add origin <https://...>`，然后直接 push 即可

可以使用 `git remote -v` 查看当前 push 和 fetch 的目的仓库情况

## pull

正常来说，通过 `git pull remote_repo_addr` 拉取下来的代码，都会保留一份远程的  **.git** 文件夹，后续每次在这个文件夹直接输入 `git pull` 可以同步更新开发者的进度

### 本地修改了代码，但是官方也修改了，并且与你的发生冲突，想要以官方的为准

1. `git fetch --all`
2. `git reset --hard origin/main`
3. `git pull`

更详细的方法参照 [版本控制](#commit)

## commit

**版本控制**，*提交(commit)* ，commit 就是在每次 push 操作中，为要修改的文件 add 之后的 commit 而得到的一个版本号

使用 `git log` 可以查看前面的某次 commit 得到的内容，使用 `git reset --hard commit_id` 来恢复到这个 commit，注意谨慎恢复。这里的 commit_id（基于 sha-1，40 位长）可以不用复制全，只要保证不重复就行，git 会自动匹配

如果不想完全恢复到某一个 commit，只想恢复某个文件(例如 main.py)，输入 `git checkout HEAD main.py` 即可恢复该文件

### 解决不同文件夹代码同步问题 ：本地和云端的代码部分存在冲突，但不想完全放弃本地的代码修改

在两个不同文件夹中都想要以 main 为主要 branch。

假设有 `A` 和 `B` 两个文件夹，且两个 branch 名称相同。某次在 `A` 上更新完代码，想同步到 `B` 文件夹，但此时的 `B` 文件夹也有代码更改，**此时不打算完全放弃掉** **`B`** **文件夹的修改内容，而是想要同时保存两个代码（例如两个不同函数都放在了相同的位置，此时只需要改一下函数位置）** ，通过 `git` 同步以后，一次性更新本地端 `A`，`B` 以及云端的 `origin`

1. 在 `A` 中正常 `git add -> git commit -> git push`，获得 `abcdef (HEAD -> main, origin/main, origin/HEAD)`
2. 在 `B` 中，自从上一次 `git pull` 过后(在 1 之前)，在本地修改过代码，按照大前提的目标，则 `git add -> git commit`，然后再 `git -> pull`，此时在本地就会提示有冲突（如果这一步使用 `git push`，会自动提示本地和云端冲突，然后拒绝 push）。
3. 此时可以在控制台的输出看到 `CONFLICT (content): Merge conflict in xxx. Automatic merge failed; fix conflicts and then commit the result.` 的回显，再打开相应的 `xxx` 文件，修改成想要的样子（在需要修改的文件会有提示什么地方冲突）。
4. 最后在 `B` 端 `git add -> git commit -> git push` 即可，若是修改正确，且两边都无冲突，则在 `A` 端再执行 `git pull`，就能成功同步 `A`，`B` 和云端的代码。

## fork

1. fork 了一个项目：原项目为 `test_account_A/test_repo_A:main`，fork 出的项目为 `test_account_B/test_repo_B:main`，将其 clone 到本地
2. 在本地新建分支 main，想要将其作为主分支，并且云端也修改成 main：`git branch main`，写点东西，`git commit -a`，`git push --set-upstream origin main`，然后到 repo 的 settings 里修改 default branch 为 main
3. 如果上游项目 `test_account_A/test_repo_A:main` 有更新，想要将其同步到自己的 main 分支，有两种方式：

    1. 手动添加映射并更新

        1. 添加原项目的映射：`git remote add src https://github.com/test_account_A/test_repo_A.git`
        2. 获取更新：`git fetch src`
        3. 本地合并：`git merge src/main`，手动解决冲突；如果自己不在 main 分支，先切换：`git checkout main`
        4. 合并完成后重新 push 到 `test_account_B/test_repo_B:main`：`git push origin main`（注意这里不要 push 到 src，不然就是人家原项目的 repo 了）
        5. 然后可以删除之：`git branch -D src`
    2. 直接通过 fork 的 main 更新

        1. 切换到与上游同步的分支：`git checkout main`
        2. 获取更新：`git pull`
        3. 切换回想要同步的分支：`git checkout main`，`git merge main`，解决冲突
        4. 更新自己的 repo：`git push origin slave`
4. pull request，如果本地有了更新，想要同步到 fork 上游的仓库做贡献

    1. 先确定在自己的仓库 `test_account_B/test_repo_B:main` 提交修改完的代码
    2. 去到仓库的 web 页面，提交合并请求（pull request），选择要合并到的分支，例如 `拉取 upstream:main 从 username:main`，等待上游所有者的合并

## fault

### git pull/fetch 时文件冲突

1. 通过 `git status` 查看 `both modified` 的项
2. `git restore --staged <path-to-file>` 将 "暂存" 状态的文件修改成 "未 add" 状态
3. 手动修改这些文件，修改完后正常 add 和 commit 即可

### 想取消 git add 的状态

说白了，`git add / rm` 就是类似于 `add / rm`，但是其修改的是本地 git repo 对项目的管理状态：

1. 当 `git add .` 时，就是把当前目录下所有内容打包，并提交到远程仓库
2. `git rm .` 时，就是删除当前目录下所有追踪

如果觉得操作错误了，想回到没有 `git add / rm` 之前的状态，就输入 `git restore --staged .`

### error: src refspec main does not match any..

```powershell
# 重命名本地仓库与远程一致
git branch -m oldBranchName newBranchName
```

### Failed to connect to github.com port 443 after ...

```powershell
# 取消全局代理，这一步是将 git 全局代理置空
git config --global --unset http.proxy
git config --global --unset https.proxy

# 如果以上两条指令还是无效，请设置成代理地址
git config --global http.proxy http://addr:port
git config --global https.proxy https://addr:port
```

### warning: LF will be replaced by CRLF in xxx.

这个报错简单理解就是，unix 使用 LF 的方式来实现换行（ascii 是 0x0a，也就是 `\n`），而 windows 使用 CR+LF（也就是 0x0d0x，`\r\n`），当在 windows 上进行修改时，一些编辑器会将 LF 修改成 CRLF

将 `core.autocrlf = input` 的作用是在 Linux 上提交时，会将所有 CRLF 转换成 LF；而在 windows 上提交时，也会强制所有文件都用 LF 提交，这样可以保持一致性

`git config --set core.autocrlf false`

### 要 push 的文件中有中文，中文被自动转码

`git config core.quotepath false`

### 每次 git push 等操作都要重新输入账号密码，想让 git 记住密码

在 cmd 里执行 `git config --global credential.helper store`，然后进行一次 `git push` 操作，输入一次账号密码，之后就会记住密码了。注意，这个方式会将你的 git 账密 **明文** 存储在 `~/.git-credentials` 里，若远程修改了 git 密码，也可以手动编辑这个文件以适配新的鉴权

### 忘记在 .gitingore 添加忽略的文件，想要删除仓库中对应的文件

在目录下 `git rm -r --cached target` 用以将 **删除仓库中 target 文件夹** 这一操作添加到暂存区，然后即可重新在  **.gitingore** 文件中配置要忽略的文件，最后 `git add . && git commit -m "sth" && git push` 即可删除远程仓库中的对应文件

### 远程仓库更名，本地想要同时修改

1. 确定远程仓库更名后的地址，例如 `https://github.com/example/new.git`
2. 进入 git 仓库目录，手动修改远程仓库地址：`git remote set-url origin https://github.com/example/new.git`

### 发现自己推送了很多小修小改的 commit, 影响仓库查看过去历史内容, 想要合并(压缩)一些 commit 记录

1. 确定当前的 branch，这里用 dev 做示例
2. 在当前分支输入：`git rebase -i 开始的commit 结束的commit`，一般使用 `git rebase -i HEAD~数量`，这里数量是数字，比如 `HEAD~5`，表示将选择从当前 commit 开始往前共 5 个 commit
3. 此时会出现编辑器，出现很多 `pick commit_id 内容`，**除了最顶上的 pick 不修改，下面的全部改成 squash**，这里可以用 vim 的快捷替换：`:%s/pick/squash/g`，`%` 表示全局查找，`s` 表示要启用替换功能，`/pick` 表示原内容，`/squash` 表示将被替换的内容，`/g` 表示全局替换。修改完后 `:wq` 保存退出。
4. 此时如果没有冲突，会发现回显是 `successfully`，表明在本地已经压缩成功。（如果没成功，请参考下面第 7 点以后的内容）
5. 压缩完成，会将此次压缩结果结合成一个 commit，会出现编辑器让你 commit 你的此次修改信息，可以在界面中看见许多被 `#` 注释的，和没被注释的内容，此时需要只能存在一个没被注释的内容，需要手动在不想保留的地方添加 `#`，这里一般是将最新的保留，也即最下面的 commit 不添加 `#`。修改完后，保存即可。（这里可以手动打开编辑器修改 `.git/COMMIT_EDITMSG` 文件，修改完后，在原来的 vim 里使用 `:e!` 来重新加载）
6. 然后使用：`git rebase --continue`、`git push -f origin dev`，表示 **强制推送** 当前已经完成了的情况到远程仓库。
7. 当然，如果出现了冲突，也不用担心。冲突时，解决冲突文件的情况（通过 vscode 等编辑器，合并冲突内容），修改完冲突后输入：`git add .`，然后再 `git rebase --continue`，就能继续操作了，回到第 5、6 步完成提交。
8. 上述操作完成后，通过 `git pull -f origin main` 来强制更新本地的主分支6

### 已经提交过很多次 commit 后，对于某个文件，不想再进行跟踪

1. 备份不想再跟踪的文件：`tar -zcvf fileName.tar.gz fileName`
2. 对不想再跟踪的文件执行：`git rm -r --cached fileName`
3. 修改 `.gitignore` 文件，添加不想再跟踪的文件，同时记得添加 `*.tar.gz` 防止跟踪压缩文档
4. 打包并推送：`git commit -m '停止跟踪文件 xxx'`，`git push`
5. 由于本地文件夹必须与云端同步，因此需要在执行完上述 `rm` 命令后再恢复文件目录：`tar -xvf fileName.tar.gz`

除此以外，还可以使用仓库清理工具来彻底删除这些文件在 commit 中的痕迹

1. 从 [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) 获取 `bfg-xxxx.jar`，将其放到仓库根路径下
2. 彻底删除某个文件：`java -jar bfg-xxxx.jar --delete-files fileName`，只要文件名即可，不需要添加其他路径
3. 彻底删除某个文件夹：`java -jar bfg-xxxx.jar --delete-folders dirName`，只需要文件夹名
4. 执行清除仓库无效引用命令：`git reflog expire --expire=now --all && git gc --prune=now --aggressive`
5. 强制推送到远程仓库：`git push --force`

### 多设备登录 git 并管理代码，配置

在新的终端上进行 push，出现以下提示：

```bash
$ git push
Username for 'https://github.com': test
Password for 'https://test@github.com': 
remote: Support for password authentication was removed on August 13, 2021.
remote: Please see https://docs.github.com/get-started/getting-started-with-git/about-remote-repositories#cloning-with-https-urls for information on currently recommended modes of authentication.
fatal: Authentication failed for 'https://github.com/test/test.git/'
```

原因是 github 删除了命令行密码登录途径，解决方法如下：

1. 参照 [仓库](https://github.com/cli/cli.git) 页面安装 github cli
2. 在终端里手动认证身份：`gh auth login`：

    ```bash
    $ gh auth login
    ? What account do you want to log into? GitHub.com
    ? What is your preferred protocol for Git operations on this host? HTTPS
    ? Authenticate Git with your GitHub credentials? Yes
    ? How would you like to authenticate GitHub CLI? Login with a web browser

    ! First copy your one-time code: XXXX-XXXX
    Press Enter to open github.com in your browser... 
    ✓ Authentication complete.
    - gh config set -h github.com git_protocol https
    ✓ Configured git protocol
    ✓ Logged in as test
    ```

    按照要求选择对应登录方式，在第四项选择 web 认证，在 web 里登录 github 账号，填入 2fa 凭证完成登录即可

### 已经 `git commit && git push` 了，但是发现作者错误（忘记 `git config --local` 修改当前账户信息），想要修改这个提交的作者

1. `git commit --amend --author="test <other@user.com>"`
2. 然后重新强制 push：`git push --force-with-lease`

### 修改单个 commit 的描述

1. `git commit --amend -m "新的描述"`
2. 然后重新强制 push：`git push --force-with-lease`

### 想要查看仓库的大小（不包含被 `.gitignore` 管理的部分）

`git count-objects -vH`

### 遇到一些仓库中带 `@` 链接符号的，一般都需要同时将这些链接的符号也 clone 下来

1. 如果没有 clone，则 `git clone --recurse-submodules https://github.com/xxx/xxx.git`，会自动下载所链接其他的仓库
2. 如果已经 clone 了，则在目录下，执行 `git submodule update --init --recursive` 来更新链接的其他仓库

### 在远程仓库修改了 default branch，本地也需要对应修改

例如在页面端从 master 改成了 main，则本地也要修改：

```bash
$ git branch -m main slave
$ git fetch origin
$ git branch -u origin/slave slave
$ git remote set-head origin -a
```

### 打印 git graph

```bash
git log --decorate=full --graph --oneline --all > /tmp/tmp/graph.txt
```


[git-problem.md](assets/git-problem-20251211153516-uo4mht1.md)