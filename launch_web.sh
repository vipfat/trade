#!/bin/bash
# 🌐 Trading Bot Web Interface Launcher
# Быстрый запуск веб-интерфейса управления ботом

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🌐 Trading Bot Web Interface Launcher                  ║"
echo "║                                                            ║"
echo "║  Полнофункциональный веб-интерфейс для управления          ║"
echo "║  AI-торговым ботом Bybit                                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Найти Python (работает и на Windows и на Linux)
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python не установлен"
    exit 1
fi

echo "🔍 Проверка Python..."
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
if [ -z "$PYTHON_VERSION" ]; then
    echo "❌ Ошибка при проверке Python"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION найден"
echo ""

# Проверка зависимостей - более гибкая проверка
echo "📦 Проверка зависимостей..."
$PYTHON_CMD -c "
import sys
missing = []
required = ['flask', 'flask_cors', 'flask_httpauth', 'dotenv', 'psutil']
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print('Отсутствуют пакеты:', ', '.join(missing))
    sys.exit(1)
else:
    print('ok')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Зависимости не установлены или неправильно установлены"
    echo ""
    echo "Переустановите зависимости:"
    echo "  pip install --upgrade --force-reinstall -r requirements.txt"
    echo ""
    exit 1
fi
echo "✓ Все зависимости установлены"
echo ""

# Проверка .env файла
echo "🔑 Проверка конфигурации..."
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден"
    echo ""
    echo "Создайте его из .env.example:"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "  copy .env.example .env"
    else
        echo "  cp .env.example .env"
    fi
    echo ""
    echo "Затем добавьте ваши API ключи от Bybit"
    echo ""
    exit 1
fi
echo "✓ Файл .env найден"
echo ""

# Запуск веб-интерфейса
echo "🚀 Запуск веб-интерфейса..."
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Веб-интерфейс запущен!"
echo ""
echo "  Откройте в браузере: http://localhost:5000"
echo ""
echo "  Учетные данные по умолчанию:"
echo "    Username: admin"
echo "    Password: admin123"
echo ""
echo "  Для остановки нажмите: Ctrl+C"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

cd "$(dirname "$0")"
python3 web_runner.py "$@"
