<#
.SYNOPSIS
Run both technique and mitigation extraction scripts sequentially.

Usage:
  .\run_all_both.ps1

This script calls `run_all_techniques.ps1` and `run_all_mitigations.ps1`.
#>

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Running techniques extraction script..."
& (Join-Path $scriptRoot 'run_all_techniques.ps1')

Write-Host "Running mitigations extraction script..."
& (Join-Path $scriptRoot 'run_all_mitigations.ps1')

Write-Host "All done."
