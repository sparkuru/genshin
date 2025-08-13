
build: `docker build -t mihomua:v1 .`

docker compose: `docker compose -f $PWD/mihomua.yml up -d`

tree like thie:

```bash
mihomua
├── config
│   ├── config.yaml
│   └── cache.db
└── mihomua.yml
```