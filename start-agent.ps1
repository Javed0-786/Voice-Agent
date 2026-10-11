# Start LiveKit Gemini Voice Agent Worker
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting LiveKit Voice Agent (Gemini Live)" -ForegroundColor Green
Write-Host " Connected to:   ws://127.0.0.1:7880" -ForegroundColor Yellow
Write-Host " Mode:           Default Room Agent (Auto-joins all rooms)" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan

python agent.py dev
