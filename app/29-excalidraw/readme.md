https://github.com/excalidraw/excalidraw

使用 [Excalidraw 社区协作方案](https://github.com/alswl/excalidraw-collaboration)部署支持实时协作和分享的内网白板

Compose 中包含前端、协作服务、存储服务、Redis 和 HTTPS 网关。

```sh
cp .env.example .env
# 将 .env 中的 EXCALIDRAW_HOST 改为客户端访问时使用的内网 IP 或域名
docker compose -f excalidraw.yaml config
docker compose -f excalidraw.yaml pull
docker compose -f excalidraw.yaml up -d
```

默认监听 `0.0.0.0:5000`，访问地址为 `https://<EXCALIDRAW_HOST>:5000/`。只开放 HTTPS 入口，前端、协作服务、存储服务和 Redis 均不直接暴露端口。

网关自动创建本地 CA 和证书，浏览器会提示证书不受信任。证书会自动续期，提示可能再次出现；证书和 CA 保存在 Docker 数据卷中。如果浏览器不允许继续访问或协作功能不可用，需要将此 CA 证书加入客户端信任列表。

