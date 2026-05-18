# Container Runtime

This project supports a containerized runtime for Hermes and DeerFlow so both can see the same local knowledge base.

## Finding Alphas

`Finding Alphas` is copyrighted. This repo does not download it automatically from unofficial sources.

To enable it legally:

```powershell
pwsh -File .\scripts\import_finding_alphas.ps1 -SourcePath C:\path\to\finding_alphas_2ed.pdf
```

That copies the PDF into:

- `knowledge_base/books/finding_alphas_2ed.pdf`

The knowledge loader already indexes PDFs from `knowledge_base/`.

## Hermes in Docker

Start Hermes:

```powershell
pwsh -File .\scripts\start_agent_containers.ps1 -StartHermes
```

Inspect:

```powershell
docker ps
docker logs wq-hermes-agent
docker exec -it wq-hermes-agent sh
docker exec -it wq-hermes-agent hermes
```

Mounted paths:

- `/workspace/knowledge_base`
- `/workspace/skills`
- `/root/.hermes/config.yaml`

## DeerFlow in Docker

Prepare and start DeerFlow:

```powershell
pwsh -File .\scripts\start_agent_containers.ps1 -StartDeerFlow
```

This uses the official upstream Docker dev stack plus a local override that mounts:

- `knowledge_base/` into the Gateway container

Monitor:

```powershell
docker compose -f .\_vendor\deer-flow\docker\docker-compose-dev.yaml -f .\_vendor\deer-flow\docker\docker-compose-dev.override.yaml ps
docker compose -f .\_vendor\deer-flow\docker\docker-compose-dev.yaml -f .\_vendor\deer-flow\docker\docker-compose-dev.override.yaml logs -f gateway
```

Expected UI:

- `http://localhost:2026`

