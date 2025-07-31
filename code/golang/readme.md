
个人的 Go 语言配置目录

```bash
golang
├── e:/lang/golang # golang 相关内容文件夹
│   ├── goroot # golang 语言相关原生工具链，完成 golang 的安装后基本不需要更改，也即 GOROOT
│   │   ├── api
│   │   ├── bin
│   │   ├── doc
│   │   ├── lib
│   │   ├── misc
│   │   ├── pkg
│   │   ├── src
│   │   └── test
│   ├── gopath # golang 第三方包等内容，后续获取到的社区包都放在这，类似 python 的 pip lib
│   ├── cache # cache 文件，即 GOCACHE:go-build 等
│   └── env
└── e:/code/godev # 可以是个人用 golang 开发的相关项目目录，将所写的项目以文件夹的方式分开，统一放在这个文件夹
    ├── project1
    ├── project2
    └── ...
```

1. 到[官网](https://go.dev/)下载对应的安装包：`go版本号.windows-amd64.msi`，msi 安装，在选择安装目录的时候可以自定义其他位置（不占用 C 盘空间，我这里是 `E:\Lang\Golang`）

2. 配置路径：

3. Windows设置 -> 查找设置中输入 "编辑系统环境变量" -> 高级 -> 环境变量

4. 在上面一栏的用户变量中新建一项，变量名为 `GOPATH`，变量值为 `e:/lang/golang/gopath`；按照这个方式再配置  `GOENV` 和 `GOCACHE`

5. 在下面一栏的系统变量中新建 `GOROOT`，变量值为 `e:/lang/golang`；

6. 同时在上下方的 `path` 一项中新建一条 `e:/lang/golang/bin`

7. 确定，保存，相关路径配置请参考上面列出来的目录信息

8. 打开 cmd，检查 go 环境配置：`go env`，这里给出几个关键参数

    ```bash
    set GOCACHE=e:/lang/golang/cache
    set GOMODCACHE=e:/lang/golang/gopath/pkg/mod	# 这个在指定了 GOPATH 后会自动配置
    set GOPATH=e:/lang/golang/gopath	# 这个就是安装各种 package 时候的目录，类似于 python 的 lib 目录
    set GOPROXY=https://proxy.golang.com.cn,direct	# 参考 python pip 安装时指定安装源
    set GOROOT=e:/lang/golang/goroot	# 即 Go 语言安装目录
    ```

9. 使用 `go env -w GOPROXY="https://proxy.golang.com.cn,direct"`（参考） 的方式来设置 go env 信息

    ```bash
    go env -w GOCACHE=e:/lang/golang/cache
    go env -w GOMODCACHE=e:/lang/golang/gopath/pkg/mod	# 这个在指定了 GOPATH 后会自动配置
    go env -w GOPATH=e:/lang/golang/gopath	# 这个就是安装各种 package 时候的目录，类似于 python 的 lib 目录
    go env -w GOPROXY=https://proxy.golang.com.cn,direct	# 参考 python pip 安装时指定安装源
    go env -w GOROOT=e:/lang/golang/goroot	# 即 Go 语言安装目录
    ```

随意编写一个 `.go` 文件测试：按照配置中的项目存放目录，到 `e:/code/godev` 目录下，首先新建一个文件夹 `HelloWorld`（一般用项目名来命名），进入到这个文件夹，使用 `go mod init sth/project1` 来初始化 `go.mod` 内容。此时在 `e:/code/godev/project1` 目录下应该有 `HelloWorld.go`，`go.mod` 两个文件

```go
// HelloWorld.go

package main

import (
    "fmt"
)

func main() {
    fmt.Println("Hello, World!")
}
```

`go.mod`：

```go
module sth/HelloWorld
go 版本号
```

后续还要写相关 project1 项目的内容时，都放在这个目录下，方便管理

在 `e:/code/godev/project1` 目录下，输入 `go run HelloWorld.go`，就能编译运行 go 程序了

linux 参考

```bash
mkdir -p $HOME/.golang/{cache,gopath}
ln -s /usr/lib/go-$(go env GOVERSION | cut -d"." -f1,2 | sed 's/go//') $HOME/.golang/goroot

go env -w GOCACHE=$HOME/.golang/cache
go env -w GOMODCACHE=$HOME/.golang/gopath/pkg/mod
go env -w GOPATH=$HOME/.golang/gopath
go env -w GOROOT=$HOME/.golang/goroot
```

