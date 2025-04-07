@echo off
echo Starting Django server in virtual environment...

REM Check if virtual environment exists, if not create it
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate

REM Check if Django is installed, if not install it
python -c "import django" 2>nul
if %errorlevel% neq 0 (
    echo Installing Django and required packages...
    pip install django pillow django-debug-toolbar
)

REM Change to the Django project directory
cd DjangoProject1

REM Run the server
echo Starting Django development server...
python manage.py runserver

REM Keep the window open if there's an error
pause 