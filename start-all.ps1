# Master Launcher: Aura Wellness Autonomous AI Voice Concierge
# Starts LiveKit Server, Voice Agent Worker, and Web Dashboard

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [Aura Wellness] Launching AI Concierge (End-to-End)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot

# Clean up port 3000 if previously occupied
$portProcess = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($portProcess) {
    Write-Host "Freeing previous server process on port 3000 (PID: $portProcess)..." -ForegroundColor Yellow
    Stop-Process -Id $portProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 1. Start LiveKit Server in a dedicated window
Write-Host "[1/3] Starting LiveKit WebRTC Server on ws://localhost:7880..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "& '$WorkspaceRoot\start-livekit.ps1'"

# Give LiveKit a brief moment to bind ports
Start-Sleep -Seconds 2

# 2. Start Gemini Autonomous Voice Agent Worker in a dedicated window
Write-Host "[2/3] Starting Gemini Multimodal Voice Agent Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "& '$WorkspaceRoot\start-agent.ps1'"

# Give Agent worker a moment to register
Start-Sleep -Seconds 2

# 3. Start Web Dashboard and Token Server
Write-Host "[3/3] Starting Web Dashboard on http://localhost:3000..." -ForegroundColor Yellow
Write-Host ""
Write-Host " Opening http://localhost:3000 in your browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

# Run web server in current terminal
python "$WorkspaceRoot\server.py"
