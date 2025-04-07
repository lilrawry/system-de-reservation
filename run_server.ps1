Write-Host "Starting Django server in virtual environment..." -ForegroundColor Green

# Check if virtual environment exists, if not create it
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Check if Django is installed, if not install it
try {
    python -c "import django" 2>$null
} catch {
    Write-Host "Installing Django and required packages..." -ForegroundColor Yellow
    pip install django pillow django-debug-toolbar
}

# Change to the Django project directory
Set-Location -Path "DjangoProject1"

# Run the server
Write-Host "Starting Django development server..." -ForegroundColor Green
python manage.py runserver

# Keep the window open if there's an error
Write-Host "Press any key to exit..." -ForegroundColor Red
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 