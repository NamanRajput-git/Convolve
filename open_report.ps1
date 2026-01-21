# Open ASHA AI Project Report in browser
# This script opens the HTML report with diagrams

$htmlFile = "ASHA_AI_Project_Report.html"
$fullPath = Join-Path $PSScriptRoot $htmlFile

if (Test-Path $fullPath) {
    Write-Host "✅ Opening project report in browser..." -ForegroundColor Green
    Write-Host "   File: $fullPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 The report includes 3 Mermaid diagrams:" -ForegroundColor Yellow
    Write-Host "   1. System Architecture" -ForegroundColor White
    Write-Host "   2. Data Flow Sequence" -ForegroundColor White
    Write-Host "   3. Memory Evolution Flowchart" -ForegroundColor White
    Write-Host ""
    Write-Host "📄 To convert to PDF:" -ForegroundColor Yellow
    Write-Host "   1. Press Ctrl+P" -ForegroundColor White
    Write-Host "   2. Select 'Save as PDF'" -ForegroundColor White
    Write-Host "   3. Enable 'Background graphics'" -ForegroundColor White
    Write-Host "   4. Click Save" -ForegroundColor White
    
    # Open in default browser
    Start-Process $fullPath
} else {
    Write-Host "❌ File not found: $htmlFile" -ForegroundColor Red
    Write-Host "   Expected location: $fullPath" -ForegroundColor Yellow
}
