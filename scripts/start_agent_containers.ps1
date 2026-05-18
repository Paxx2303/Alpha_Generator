param(
    [switch]$StartHermes,
    [switch]$StartDeerFlow
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $env:HOME -and $env:USERPROFILE) {
    $env:HOME = $env:USERPROFILE
}

if ($StartHermes) {
    New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "logs\hermes") | Out-Null
    docker compose -f (Join-Path $projectRoot "docker-compose.agents.yml") up -d hermes-agent
}

if ($StartDeerFlow) {
    & (Join-Path $projectRoot "scripts\prepare_deerflow_container.ps1")
    $deerRoot = Join-Path $projectRoot "_vendor\deer-flow"
    $env:DEER_FLOW_ROOT = $deerRoot.Replace('\', '/')
    docker compose `
      -f (Join-Path $deerRoot "docker\docker-compose-dev.yaml") `
      -f (Join-Path $deerRoot "docker\docker-compose-dev.override.yaml") `
      up -d --build nginx frontend gateway
}
