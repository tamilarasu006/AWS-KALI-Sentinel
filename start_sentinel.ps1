# PowerShell starter script for KALI Sentinel Backend Server
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Test-Path "$scriptDir\src") {
    $projectDir = $scriptDir
} elseif (Test-Path "$scriptDir\OpenDemon-main\src") {
    $projectDir = "$scriptDir\OpenDemon-main"
} else {
    $projectDir = "E:\Demon-sentinel\OpenDemon-main"
}

$env:PYTHONPATH = "$projectDir\src"
Write-Host "Starting KALI Sentinel Backend from $projectDir..." -ForegroundColor Cyan

& "$projectDir\.venv\Scripts\python.exe" -m kali_sentinel.server.routes
