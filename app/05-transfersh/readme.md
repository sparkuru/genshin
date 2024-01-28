# transfer.sh

repo：[dutchcoders/transfer.sh](https://github.com/dutchcoders/transfer.sh.git)

docker：`dutchcoders/transfer.sh:latest`、`dutchcoders/transfer.sh:latest-noroot`

目前有一个需求是在宿主机使用非 root 权限时能够看到 transfer.sh 镜像里上传的文件，默认的两个镜像都没法很好地实现这个需求，解决方法如下：

`dutchcoders/transfer.sh:latest-noroot` 默认使用 `uid = 5000 / gid = 5000` 来作为文件权限，想要修改成 `1000 / 1000` 就需要自己获取镜像后自定义创建一份，基本逻辑是在创建时使用 `docker build -t transfersh-user --build-arg RUNAS=any --build-arg PUID=1000 --build-arg PGID=1000 .`

1. `git clone https://github.com/dutchcoders/transfer.sh.git repo`，`cd repo`
2. `docker build -t transfersh-user --build-arg RUNAS=any --build-arg PUID=1000 --build-arg PGID=1000 .`
3. 出现 *Successfully tagged transfersh-user:latest* 即为成功构建
4. 在 `docker-compose.yml` 里使用 `image: transfersh-user:latest` 即可