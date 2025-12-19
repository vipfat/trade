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

# Проверка Python
echo "🔍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION найден"
echo ""

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Зависимости не установлены"
    echo ""
    echo "Установите их командой:"
    echo "  pip install -r requirements.txt"
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
    echo "  cp .env.example .env"
    echo "  nano .env"
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
