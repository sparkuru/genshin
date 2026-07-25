# Oh My OpenCode

Repository-managed configuration for Oh My OpenCode (OMO). The tracked source of truth is `config/oh-my-openagent.json`; `link-config.sh` links it to OpenCode's user configuration directory.

## Install

Install OpenCode and Bun, then install the OMO plugin:

```bash
bunx oh-my-openagent install
```

Authenticate the configured providers in OpenCode:

```text
/connect -> OpenAI -> ChatGPT Plus/Pro
/connect -> OpenCode Go
```

Link this repository-managed configuration. The first run preserves the existing local configuration before replacing it with a symbolic link:

```bash
./link-config.sh --backup-existing
```

Check the final setup:

```bash
bunx oh-my-openagent doctor --json
```

## Role Routing

| Role | Model | Responsibility |
|---|---|---|
| `sisyphus` | GPT-5.6 Terra / high | Main coordinator: interpret requests, decompose work, and delegate. |
| `atlas` | GPT-5.6 Terra / high | Execute plans, coordinate workers, and verify progress. |
| `prometheus` | GPT-5.6 Sol / high | Clarify requirements and produce implementation plans. |
| `metis` | GPT-5.6 Sol / medium | Review plans for gaps and feasibility. |
| `oracle` | GPT-5.6 Sol / high | Read-only architecture and difficult-problem analysis. |
| `momus` | GPT-5.6 Terra / high | Read-only plan and result review. |
| `hephaestus` | DeepSeek V4 Pro / high | Autonomous deep implementation and repair. |
| `sisyphus-junior` | DeepSeek V4 Pro / high | Focused coding, tests, and verification. |
| `librarian` | GPT-5.3 Codex Spark / low | Read-only documentation and codebase research. |
| `explore` | GPT-5.3 Codex Spark / low | Read-only repository exploration and fast search. |
| `multimodal-looker` | GPT-5.6 Sol / low | Read-only image, screenshot, and UI analysis. |

## Task Categories

Categories select a model and reasoning level for delegated work. They are not additional agents.

| Category | Model | Use |
|---|---|---|
| `quick` | GPT-5.3 Codex Spark / low | Small fixes and simple edits. |
| `unspecified-low` | GPT-5.3 Codex Spark / low | Low-complexity general work. |
| `writing` | GPT-5.3 Codex Spark / medium | Documentation and technical prose. |
| `unspecified-high` | DeepSeek V4 Pro / max | High-complexity general implementation. |
| `deep` | GPT-5.6 Terra / xhigh | One difficult goal requiring deep investigation. |
| `ultrabrain` | GPT-5.6 Sol / high | Architecture and complex reasoning. |
| `visual-engineering` | GPT-5.6 Sol / high | Frontend, UI/UX, and visual engineering. |
| `artistry` | GPT-5.6 Sol / high | Creative and design-oriented work. |

## Read the Active Configuration

Inspect the repository source:

```bash
jq '.agents' config/oh-my-openagent.json
jq '.categories' config/oh-my-openagent.json
```

Confirm that OpenCode reads the linked file:

```bash
readlink -f ~/.config/opencode/oh-my-openagent.json
```

Inspect OMO's effective model resolution, including fallbacks:

```bash
bunx oh-my-openagent doctor --json
```

All primary models and fallback chains are constrained to GPT-5.3 Codex Spark, GPT-5.6 Terra, GPT-5.6 Sol, and DeepSeek V4 Pro.
