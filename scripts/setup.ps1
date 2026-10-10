$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$bundledRoot = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies'
$pythonBin = Join-Path $bundledRoot 'python/python.exe'
$pnpmBin = Join-Path $bundledRoot 'bin/fallback/pnpm.cmd'
if (-not (Test-Path -LiteralPath $pythonBin)) { $pythonBin = 'python' }
if (-not (Test-Path -LiteralPath $pnpmBin)) { $pnpmBin = 'pnpm' }
& $pythonBin -m pip install --target .python-deps -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Installation Python interrompue.' }
& $pnpmBin install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw 'Installation frontend interrompue.' }
$env:PYTHONPATH = "$projectRoot/.python-deps;$projectRoot"
if (-not (Test-Path -LiteralPath 'data/processed/sncf.sqlite')) {
    & $pythonBin scripts/import_data.py
    if ($LASTEXITCODE -ne 0) { throw 'Import des sources interrompu.' }
}
Write-Host 'Prêt. Lancez : node scripts/dev.mjs'
