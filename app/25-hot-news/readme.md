
repo: https://github.com/orz-ai/hot_news.git

## docker

(optional) use `./init.sh` to init the docker files

or manually:

1. `git clone https://github.com/orz-ai/hot_news.git repo`
2. `touch hot-news.yaml`, see [hot-news.yaml](./hot-news.yaml)
3. `touch Dockerfile`, see [Dockerfile](./Dockerfile)
4. diy own config: `cp repo/config/config.yaml config/config.docker.yaml`, specific like this:
   ```yaml
   database:
     host: "mysql"
     user: "news_app"
     password: "news_app_secret"
     db: "news_crawler"
     charset: "utf8mb4"
     autocommit: true


   redis:
     host: "redis"
     port: 6379
     db: 0
     password: ""
     decode_responses: false
     socket_timeout: 5
     socket_connect_timeout: 5
     health_check_interval: 30
   ```
5. `docker compose -f hot-news.yaml build`
6. `docker compose -f hot-news.yaml up -d`

then try: `GET http://127.0.0.1:18080/api/v1/dailynews/?platform=hackernews | jq`

get doc via: `GET http://127.0.0.1:18080/docs`