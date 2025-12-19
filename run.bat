@echo off
REM 🌐 Trading Bot Web Interface Launcher for Windows
REM Простой запуск веб-интерфейса на Windows

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     🌐 Trading Bot Web Interface Launcher                  ║
echo ║                                                            ║
echo ║  Полнофункциональный веб-интерфейс для управления          ║
echo ║  AI-торговым ботом Bybit                                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Проверка Python
echo 🔍 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен или недоступен в PATH
    echo.
    echo Установите Python с сайта https://www.python.org/
    echo При установке обязательно отметьте "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION% найден
echo.

REM Проверка зависимостей
echo 📦 Проверка зависимостей...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ❌ Зависимости не установлены
    echo.
    echo Установите их командой:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo ✓ Flask найден

python -c "import flask_cors" >nul 2>&1
if errorlevel 1 (
    echo ✗ Flask-CORS не установлен
    goto install_deps
)
echo ✓ Flask-CORS найден

python -c "import flask_httpauth" >nul 2>&1
if errorlevel 1 (
    echo ✗ Flask-HTTPAuth не установлен
    goto install_deps
)
echo ✓ Flask-HTTPAuth найден

echo ✓ Все зависимости установлены
echo.

REM Проверка .env файла
echo 🔑 Проверка конфигурации...
if not exist ".env" (
    echo ⚠️  Файл .env не найден
    echo.
    echo Создайте его из .env.example:
    echo   copy .env.example .env
    echo.
    echo Затем отредактируйте .env и добавьте API ключи от Bybit
    echo.
    pause
    exit /b 1
)
echo ✓ Файл .env найден
echo.

REM Запуск Flask
echo 🚀 Запуск веб-интерфейса...
echo.

for /f "tokens=*" %%i in ('python -c "import os; print(os.getenv('ADMIN_USERNAME', 'admin'))"') do set ADMIN_USER=%%i
for /f "tokens=*" %%i in ('python -c "import os; print(os.getenv('ADMIN_PASSWORD', 'admin123'))"') do set ADMIN_PASS=%%i

echo ================================================================================
echo ✅ Веб-интерфейс запущен!
echo.
echo   🌐 Откройте: http://127.0.0.1:5000
echo   📝 Логин: %ADMIN_USER%
echo   🔐 Пароль: %ADMIN_PASS%
echo.
echo   Нажмите Ctrl+C для остановки
echo.
echo ================================================================================
echo.

python run.py
pause
exit /b 0

:install_deps
echo.
echo Переустановите зависимости командой:
echo   pip install --upgrade -r requirements.txt
echo.
pause
exit /b 1
