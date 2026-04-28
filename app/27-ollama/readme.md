
repo: https://github.com/ollama/ollama.git

## usage

build first: `docker compose -f ollama.yaml build`

list models: `docker compose -f ollama.yaml run --rm ollama-cli models`


```bash
# single io
docker compose -f ollama.yaml run --rm ollama-cli chat -m nemotron-3-nano:latest "bonjour"

# chat prompt
docker compose -f ollama.yaml run --rm ollama-cli chat -m nemotron-3-nano:latest
```

## connect to remote ollama server

```bash
export OLLAMA_BASE_URL="http://127.0.0.1:11434"

python3 repo/ollama_cli.py models
python3 repo/ollama_cli.py chat -m nemotron-3-nano:4b "bonjour"
```
