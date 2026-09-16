# NexAlert Demo Startup (Windows PowerShell)
# OPTIMIZED FOR PRESENTATION

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      NEXALERT DEMO STARTUP             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Kill any existing instances on these ports
Write-Host "→ Cleaning existing services..." -ForegroundColor Yellow
$ports = @(8000, 3000, 3001)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 1

# Start Backend
Write-Host "→ Starting Backend API..." -ForegroundColor Yellow
$backendPath = "services\backend"
if (Test-Path "$backendPath\venv\Scripts\python.exe") {
    $pythonExe = "$backendPath\venv\Scripts\python.exe"
} else {
    $pythonExe = "python"
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $backendPath; & '$pythonExe' -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Minimized
Write-Host "  Backend starting on http://localhost:8000" -ForegroundColor Green

# Wait for backend health
Write-Host "  Waiting for backend..." -ForegroundColor Gray
for ($i = 1; $i -le 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
        Write-Host "✓ Backend ready" -ForegroundColor Green
        break
    } catch {
        if ($i -eq 15) {
            Write-Host "⚠ Backend slow to start, continuing anyway..." -ForegroundColor Yellow
        }
    }
}

# Start Authority Dashboard
Write-Host "→ Starting Authority Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps\authority-dashboard; npm run dev" -WindowStyle Minimized
Write-Host "  Dashboard starting on http://localhost:3000" -ForegroundColor Green
Start-Sleep -Seconds 2

# Start Citizen Emergency UI
Write-Host "→ Starting Citizen Emergency UI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PORT='3001'; cd apps\citizen-web; npm run dev" -WindowStyle Minimized
Write-Host "  Citizen UI starting on http://localhost:3001" -ForegroundColor Green
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║      NEXALERT DEMO READY ✓             ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "URLS:" -ForegroundColor Cyan
Write-Host "  Authority Dashboard:  " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor White
Write-Host "  Citizen Emergency:    " -NoNewline; Write-Host "http://localhost:3001" -ForegroundColor White
Write-Host "  Backend API:          " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor White
Write-Host "  API Documentation:    " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "DEMO CONTROLS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Trigger Fire Scenario:" -ForegroundColor Yellow
Write-Host "    Invoke-RestMethod -Method POST http://localhost:8000/demo/trigger-fire"
Write-Host ""
Write-Host "  Reset to Normal:" -ForegroundColor Yellow
Write-Host "    Invoke-RestMethod -Method POST http://localhost:8000/demo/reset"
Write-Host ""
Write-Host "  Check Status:" -ForegroundColor Yellow
Write-Host "    Invoke-RestMethod http://localhost:8000/demo/status"
Write-Host ""
Write-Host "PRESENTATION FLOW:" -ForegroundColor Cyan
Write-Host "  1. Open Authority Dashboard (http://localhost:3000)"
Write-Host "  2. Show normal telemetry from NEX-001"
Write-Host "  3. Trigger fire scenario using command above"
Write-Host "  4. Show incident detection in dashboard"
Write-Host "  5. Open Citizen Emergency (http://localhost:3001)"
Write-Host "  6. Show critical alert for citizens"
Write-Host "  7. Reset when done"
Write-Host ""
Write-Host "Services running in minimized windows." -ForegroundColor Gray
Write-Host "Close PowerShell windows to stop services." -ForegroundColor Gray
Write-Host ""
