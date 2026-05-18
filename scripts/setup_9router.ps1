param(
    [string]$HermesHome = "$HOME\.hermes",
    [string]$DeerFlowRoot = "",
    [switch]$WriteProjectEnv
)

$ErrorActionPreference = "Stop"

function Copy-TemplateWithBackup {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    if (Test-Path -LiteralPath $Destination) {
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        Copy-Item -LiteralPath $Destination -Destination "$Destination.$timestamp.bak" -Force
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$hermesTemplate = Join-Path $projectRoot "config\hermes.9router.example.yaml"
$deerflowTemplate = Join-Path $projectRoot "config\deerflow.9router.example.yaml"

Copy-TemplateWithBackup -Source $hermesTemplate -Destination (Join-Path $HermesHome "config.yaml")

$hermesEnvPath = Join-Path $HermesHome ".env"
if (-not (Test-Path -LiteralPath $hermesEnvPath)) {
    New-Item -ItemType File -Path $hermesEnvPath -Force | Out-Null
}

$hermesEnvContent = Get-Content -LiteralPath $hermesEnvPath -Raw -ErrorAction SilentlyContinue
if ($hermesEnvContent -notmatch "(?m)^NINE_ROUTER_BASE_URL=") {
    Add-Content -LiteralPath $hermesEnvPath -Value "NINE_ROUTER_BASE_URL=http://localhost:20128/v1"
}
if ($hermesEnvContent -notmatch "(?m)^NINE_ROUTER_API_KEY=") {
    Add-Content -LiteralPath $hermesEnvPath -Value "NINE_ROUTER_API_KEY=dummy"
}
if ($hermesEnvContent -notmatch "(?m)^HERMES_MODEL_NAME=") {
    Add-Content -LiteralPath $hermesEnvPath -Value "HERMES_MODEL_NAME=oc/nemotron-3-super-free"
}

if ($DeerFlowRoot) {
    $resolvedDeerFlowRoot = (Resolve-Path $DeerFlowRoot).Path
    Copy-TemplateWithBackup -Source $deerflowTemplate -Destination (Join-Path $resolvedDeerFlowRoot "config.yaml")

    $deerEnvPath = Join-Path $resolvedDeerFlowRoot ".env"
    if (-not (Test-Path -LiteralPath $deerEnvPath)) {
        New-Item -ItemType File -Path $deerEnvPath -Force | Out-Null
    }

    $deerEnvContent = Get-Content -LiteralPath $deerEnvPath -Raw -ErrorAction SilentlyContinue
    if ($deerEnvContent -notmatch "(?m)^NINE_ROUTER_BASE_URL=") {
        Add-Content -LiteralPath $deerEnvPath -Value "NINE_ROUTER_BASE_URL=http://localhost:20128/v1"
    }
    if ($deerEnvContent -notmatch "(?m)^NINE_ROUTER_API_KEY=") {
        Add-Content -LiteralPath $deerEnvPath -Value "NINE_ROUTER_API_KEY=dummy"
    }
    if ($deerEnvContent -notmatch "(?m)^DEERFLOW_MODEL_NAME=") {
        Add-Content -LiteralPath $deerEnvPath -Value "DEERFLOW_MODEL_NAME=oc/nemotron-3-super-free"
    }
}

if ($WriteProjectEnv) {
    $projectEnv = Join-Path $projectRoot ".env"
    if (-not (Test-Path -LiteralPath $projectEnv)) {
        Copy-Item -LiteralPath (Join-Path $projectRoot ".env.example") -Destination $projectEnv -Force
    }

    $projectEnvContent = Get-Content -LiteralPath $projectEnv -Raw -ErrorAction SilentlyContinue
    if ($projectEnvContent -notmatch "(?m)^NINE_ROUTER_BASE_URL=") {
        Add-Content -LiteralPath $projectEnv -Value "NINE_ROUTER_BASE_URL=http://localhost:20128/v1"
    }
    if ($projectEnvContent -notmatch "(?m)^NINE_ROUTER_API_KEY=") {
        Add-Content -LiteralPath $projectEnv -Value "NINE_ROUTER_API_KEY=dummy"
    }
}

Write-Host "Hermes configured at $HermesHome\config.yaml"
if ($DeerFlowRoot) {
    Write-Host "DeerFlow configured at $resolvedDeerFlowRoot\config.yaml"
}
if ($WriteProjectEnv) {
    Write-Host "Project .env updated with 9Router defaults"
}
