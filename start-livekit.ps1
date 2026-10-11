# Start LiveKit Server in Development Mode
# Runs WebRTC SFU on ws://localhost:7880
# Default Dev Credentials:
#   API Key: devkey
#   API Secret: secret

$BinPath = Join-Path $PSScriptRoot "bin\livekit-server.exe"

if (-Not (Test-Path $BinPath)) {
    Write-Error "livekit-server.exe not found at $BinPath"
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting LiveKit Server (Development Mode)" -ForegroundColor Green
Write-Host " WebSocket URL:  ws://localhost:7880" -ForegroundColor Yellow
Write-Host " API Key:        devkey" -ForegroundColor Yellow
Write-Host " API Secret:     secret" -ForegroundColor Yellow
Write-Host " Test UI:        https://example.livekit.io" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

& $BinPath --dev
