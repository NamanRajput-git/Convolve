# Create .env file from template
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file. Please edit it and add your GOOGLE_API_KEY"
} else {
    Write-Host "⚠️  .env file already exists"
}

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion"
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+"
    exit 1
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..."
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully"
} else {
    Write-Host "❌ Failed to install dependencies"
    exit 1
}

# Check Qdrant
Write-Host "`n🔍 Checking for Qdrant..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/collections" -Method GET -ErrorAction Stop
    Write-Host "✅ Qdrant is running"
} catch {
    Write-Host "⚠️  Qdrant not detected. Starting with Docker..."
    docker run -d -p 6333:6333 qdrant/qdrant
    Start-Sleep -Seconds 5
    Write-Host "✅ Qdrant started on port 6333"
}

Write-Host "`n📚 Seeding medical knowledge base..."
python medical_knowledge_seed.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Knowledge base seeded"
} else {
    Write-Host "⚠️  Knowledge seeding failed, but you can continue"
}

Write-Host "`n✨ Setup complete!"
Write-Host "`nNext steps:"
Write-Host "1. Edit .env file and add your GOOGLE_API_KEY"
Write-Host "2. Run: streamlit run app.py"
Write-Host "`nEnjoy ASHA AI! 🏥"
