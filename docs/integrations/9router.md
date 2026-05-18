# 9Router Integration

This project can route both Hermes and DeerFlow through the same local 9Router OpenAI-compatible endpoint.

## Why this setup

- 9Router exposes a local OpenAI-compatible endpoint at `http://localhost:20128/v1`.
- Hermes supports any OpenAI-compatible custom endpoint through `~/.hermes/config.yaml`.
- DeerFlow supports OpenAI-compatible models in `config.yaml` and can load a custom config path from `DEER_FLOW_CONFIG_PATH`.

## Files in this repo

- `config/hermes.9router.example.yaml`
- `config/deerflow.9router.example.yaml`
- `scripts/setup_9router.ps1`

## Quick setup

1. Install and start 9Router.
2. In the 9Router dashboard, enable a free Qwen route.
3. Run:

```powershell
pwsh -File .\scripts\setup_9router.ps1 -DeerFlowRoot C:\path\to\deer-flow -WriteProjectEnv
```

4. Optional: set a different free Qwen model by overriding:

```powershell
$env:HERMES_MODEL_NAME = "Qwen/Qwen3-Coder-480B-A35B-Instruct"
$env:DEERFLOW_MODEL_NAME = "Qwen/Qwen3-Coder-480B-A35B-Instruct"
```

## Notes

- `NINE_ROUTER_API_KEY=dummy` is included because many OpenAI-compatible clients require a non-empty key field even for a local gateway.
- DeerFlow should be launched with `DEER_FLOW_CONFIG_PATH` or from its project root if it does not automatically pick up the generated config.
- Hermes reads `~/.hermes/config.yaml` as the source of truth for provider, model, and base URL.
