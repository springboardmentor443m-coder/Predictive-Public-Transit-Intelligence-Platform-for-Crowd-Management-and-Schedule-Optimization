Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  MetroFlow AI Metro Management & Scheduling Platform" -ForegroundColor Green
Write-Host "  Location: $PSScriptRoot" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot/backend'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot/frontend'; npm run dev"

Write-Host "`nMetroFlow servers launched successfully!" -ForegroundColor Green
Write-Host "Open: http://localhost:5173" -ForegroundColor Cyan
Write-Host "API:  http://127.0.0.1:8000/docs" -ForegroundColor Gray
