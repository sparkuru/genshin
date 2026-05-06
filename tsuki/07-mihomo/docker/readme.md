
build: `docker build -t mihomua:v1 .`

docker compose: `docker compose -f $PWD/mihomua.yaml up -d`

tree like thie:

```bash
mihomua
├── config
│   ├── config.yaml
│   └── cache.db
└── mihomua.yml
```