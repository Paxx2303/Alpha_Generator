param(
    [string]$DeerFlowRoot = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $DeerFlowRoot) {
    $DeerFlowRoot = Join-Path $projectRoot "_vendor\deer-flow"
}
$deerRoot = (Resolve-Path $DeerFlowRoot).Path

$configSource = Join-Path $projectRoot "config\deerflow.9router.container.yaml"
$configTarget = Join-Path $deerRoot "config.yaml"
$envTarget = Join-Path $deerRoot ".env"
$frontendEnvTarget = Join-Path $deerRoot "frontend\.env"
$extSource = Join-Path $deerRoot "extensions_config.example.json"
$extTarget = Join-Path $deerRoot "extensions_config.json"
$frontendEnvSource = Join-Path $deerRoot "frontend\.env.example"

Copy-Item -LiteralPath $configSource -Destination $configTarget -Force
if (-not (Test-Path -LiteralPath $extTarget)) {
    Copy-Item -LiteralPath $extSource -Destination $extTarget -Force
}
if (-not (Test-Path -LiteralPath $frontendEnvTarget)) {
    Copy-Item -LiteralPath $frontendEnvSource -Destination $frontendEnvTarget -Force
}

$envLines = @(
    "NINE_ROUTER_BASE_URL=http://host.docker.internal:20128/v1"
    "NINE_ROUTER_API_KEY=dummy"
    "DEERFLOW_MODEL_NAME=oc/nemotron-3-super-free"
    "DEER_FLOW_ROOT=$deerRoot".Replace('\', '/')
)
$envLines | Set-Content -LiteralPath $envTarget -Encoding UTF8

Write-Host "Prepared DeerFlow container config at $deerRoot"
