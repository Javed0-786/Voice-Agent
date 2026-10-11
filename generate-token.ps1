param(
    [string]$Room = "demo-room",
    [string]$Identity = "user-" + (Get-Random -Minimum 1000 -Maximum 9999),
    [string]$ApiKey = "devkey",
    [string]$ApiSecret = "secret",
    [string]$ValidFor = "24h"
)

$LkPath = Join-Path $PSScriptRoot "bin\lk.exe"

if (-Not (Test-Path $LkPath)) {
    Write-Error "lk.exe not found at $LkPath"
    exit 1
}

Write-Host "Generating LiveKit Access Token..." -ForegroundColor Cyan
Write-Host "  Room:     $Room" -ForegroundColor Yellow
Write-Host "  Identity: $Identity" -ForegroundColor Yellow

$token = & $LkPath token create --api-key $ApiKey --api-secret $ApiSecret --join --room $Room --identity $Identity --valid-for $ValidFor

Write-Host ""
Write-Host "Token generated:" -ForegroundColor Green
Write-Host $token -ForegroundColor White
Write-Host ""
Write-Host "Connect to server at: ws://localhost:7880" -ForegroundColor Cyan
Write-Host "Use in LiveKit playground: https://example.livekit.io" -ForegroundColor Cyan
