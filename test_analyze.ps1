$body = '{"request":"Check open ports on my authorized lab server","target":"localhost","authorized":true}'
Write-Host "=== 1. Direct Backend Test (http://127.0.0.1:8000/v1/sentinel/analyze) ===" -ForegroundColor Cyan
$res1 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/sentinel/analyze" -Method Post -Body $body -ContentType "application/json"
$res1 | ConvertTo-Json -Depth 4

Write-Host "`n=== 2. Frontend Proxy Test (http://localhost:5173/v1/sentinel/analyze) ===" -ForegroundColor Cyan
$res2 = Invoke-RestMethod -Uri "http://localhost:5173/v1/sentinel/analyze" -Method Post -Body $body -ContentType "application/json"
$res2 | ConvertTo-Json -Depth 4
