# siyuan-note

一份笔记，希望在工作笔记本、mac、家里主机、手机上都能实时编辑、查看，又要保证绝对的私密性，最后打算尝试 [思源笔记](https://github.com/siyuan-note/siyuan.git)

- 优势：

  1. 跨平台：Linux、Windows、Android / iOS、MacOS
  2. 易部署：docker、application / dmg、apk
  3. 隐私性：端对端加密，可自建服务器、也可以使用自定义的服务器例如阿里云 oss
  4. 可玩性：丰富插件、社区
  5. 快速集成 ai，可以直接调用 openai、azure 的 api，也可以自己本地 ollama 使用

- 劣势：

  1. 私有文件格式，但是可以导出成各种类型文件格式，包括 markdown
  2. 使用同步功能需要购买 [会员](https://b3log.org/siyuan/pricing.html)

## 1、同步

推荐使用 阿里云、腾讯云、七牛云 等的 oss 服务，需要购买终身会员（64 RMB），下面以 阿里云 OSS 为例

1. 参考 [思源使用阿里云 OSS 同步详细教程](https://b3logfile.com/pdf/article/1668749494228.pdf) 流程
2. 有几个地方需要特别注意一下

    1. 建议新建一个新的 bucket 来存放思源的文件，与原有的作其他用途 bucket 做权限分离（例如还有其他可供公共读的图床 bucket）
    2. 在授权子用户时，建议开启 https 访问
3. 云端配置的参考如下：

    | 类型            | 值                                                           | 备注                                                                      |
    | ----------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------- |
    | Endpoint        | oss-cn-shenzhen.aliyuncs.com                                 |                                                                           |
    | Access Key      | LTAI5t••••••••••••••••••••••           |                                                                           |
    | Secret Key      | •••••••••••••••••••••••••••••• |                                                                           |
    | Bucket          | wkyuu-siyuan                                                 |                                                                           |
    | Region          | shenzhen                                                     |                                                                           |
    | Timeout         | 60                                                           |                                                                           |
    | Addressing      | Virtual-hosted-style                                         |                                                                           |
    | TLS Verify      | Verify                                                       | 除去思源对数据的本地端到端加密外，还有一层来自 OSS 的 TLS 加密，防止 MITM |
    | Concurrent Reqs | 8                                                            |                                                                           |
4. 同步

    1. s3 的配置完成并同步后，可以将配置文件导出成 `xxxxx.json.zip` 文件，快速一键配置
    2. 除此之外还要在 `关于` 中生成一个密钥，在其他地方导入需要该密钥
5. 除此之外，还建议配置端到端加密的密钥，直接使用一个自己的主密钥进行生成即可

## 2、图床

利用 cors 配置 + picgo 插件的 cors 代理，可以解决以下问题：

1. 在写文章时把图片插入到笔记里，然后用 picgo 上传到 oss 后替换成链接表示，也方便直接复制到博客中
2. 本地多端写笔记时可以正常看到图片，博客中也可以正常看到图片
3. 其他人、包括自己单独直接拿出图片链接则无法访问图片

操作方法如下：

1. 按照前文一样，正常配置 bucket，并创建一个文件夹路径，这里是 `markdown`
2. 选择对应的 bucket 后，在 `访问控制 RAM` 中

    1. 阻止公共访问
    2.

## 3、快捷键

参考 typora 常用的快捷键，我这里做了一些快捷键上的配置，只保留以下几个快捷键，其他全部清空

| 类型          | 功能           | 按键                     |
| --------------- | ---------------- | -------------------------- |
| 通用          | 替换           | ctrl + h                 |
|               | 关闭当前标签页 | ctrl + w                 |
|               | 文档树         | ctrl + shift + \\     |
|               | 全局搜索       | ctrl + f                 |
|               |                |                          |
| 编辑器 / 通用 | 大纲           | ctrl + \\             |
|               | 复制纯文本     | ctrl + shift + c         |
|               | 撤销           | ctrl + z                 |
|               | 重做           | ctrl + shift + z         |
|               | 重命名         | f2                       |
|               |                |                          |
| 元素          | 粗体           | ctrl + b                 |
|               | 斜体           | ctrl + i                 |
|               | 下划线         | ctrl + u                 |
|               | 删除线         | shift + alt + 5          |
|               | 表格           | ctrl + t                 |
|               |                |                          |
| 标题          | 1-6 级标题     | ctrl + 1-6               |
|               |                |                          |
| 表格          | 在下方插入一行 | ctrl + enter             |
|               | 删除行         | ctrl + shift + backspace |

# 4、其他配置

1. 主题
2. 其他好用的插件

## refer

1. 阿里云 OSS 设置跨域访问，https://www.cnblogs.com/weifeng1463/p/9120442.html