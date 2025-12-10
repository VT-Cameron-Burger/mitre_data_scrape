<#
.SYNOPSIS
Run text extraction for all mitigation URLs and store outputs in a dedicated folder.

Usage:
  .\run_all_mitigations.ps1

This script will prefer the repository virtualenv at `.venv\Scripts\python.exe` if present,
falling back to `python` on PATH. It creates `text_outputs_mitigations` in the repo root.
#>

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot '..')

$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPython) { $python = $venvPython } else { $python = 'python' }

$inputFile = Join-Path $repoRoot 'mitre_mitigation_urls.txt'
if (-not (Test-Path $inputFile)) {
    Write-Error "Input file not found: $inputFile"
    exit 1
}

$outDir = Join-Path $repoRoot 'text_outputs_mitigations'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

Write-Host "Running extraction for mitigations..."
& $python "$repoRoot\scripts\save_urls_to_texts.py" --inputs $inputFile --output $outDir --workers 4

Write-Host "Done. Outputs in: $outDir"
