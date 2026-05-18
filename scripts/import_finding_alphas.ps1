param(
    [string]$SourcePath = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$targetDir = Join-Path $projectRoot "knowledge_base\books"
$targetPath = Join-Path $targetDir "finding_alphas_2ed.pdf"

if (-not $SourcePath) {
    $envFile = Join-Path $projectRoot ".env"
    if (Test-Path -LiteralPath $envFile) {
        $match = Select-String -Path $envFile -Pattern "^FINDING_ALPHAS_PDF_PATH=(.+)$" | Select-Object -First 1
        if ($match) {
            $SourcePath = $match.Matches[0].Groups[1].Value.Trim()
        }
    }
}

if (-not $SourcePath) {
    throw "No source PDF provided. Pass -SourcePath or set FINDING_ALPHAS_PDF_PATH in .env."
}

$resolvedSource = (Resolve-Path $SourcePath).Path
if (-not (Test-Path -LiteralPath $resolvedSource)) {
    throw "Source PDF not found: $SourcePath"
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -LiteralPath $resolvedSource -Destination $targetPath -Force

$notePath = Join-Path $targetDir "finding_alphas_2ed.source.txt"
@(
    "Imported from: $resolvedSource"
    "Imported at: $(Get-Date -Format s)"
) | Set-Content -LiteralPath $notePath -Encoding UTF8

Write-Host "Imported Finding Alphas to $targetPath"

