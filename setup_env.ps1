# PowerShell script to set up virtual environment for Windows
Write-Host "Setting up virtual environment..." -ForegroundColor Green

# Create virtual environment
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "Setup complete! Virtual environment is activated." -ForegroundColor Green
Write-Host "To activate in future sessions, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow

