#!/bin/bash
# Стартовый скрипт для Linux/Mac

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║    🤖 AI TRADING BOT - Стартовый скрипт для Linux/Mac 🤖     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Проверка Python
echo "🔍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не найден!"
    echo "Установите Python 3.10+ с https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Найден: $PYTHON_VERSION"
echo ""

# Проверка зависимостей
echo "📦 Установка зависимостей..."
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Зависимости установлены"
else
    echo "❌ Ошибка при установке зависимостей"
    exit 1
fi
echo ""

# Меню выбора
echo "════════════════════════════════════════════════════════════════"
echo "  Выберите что запустить:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1️⃣  Интерактивное меню (рекомендуется)"
echo "2️⃣  Веб-интерфейс + бот на testnet"
echo "3️⃣  Только веб-интерфейс"
echo "4️⃣  Только бот на testnet"
echo "5️⃣  Демонстрация возможностей"
echo "6️⃣  Полная проверка системы"
echo "7️⃣  Выход"
echo ""

read -p "Введите номер (1-7): " choice

echo ""

case $choice in
    1)
        echo "▶ Запуск интерактивного меню..."
        python3 quickstart.py
        ;;
    2)
        echo "▶ Запуск веб-интерфейса + бота..."
        echo ""
        echo "🌐 Веб-интерфейс будет доступен на:"
        echo "   http://localhost:5000 (логин: admin, пароль: admin123)"
        echo ""
        echo "⏬ Запустите в другом терминале для запуска бота:"
        echo "   python3 main.py --pairs 20 --testnet"
        echo ""
        python3 run.py
        ;;
    3)
        echo "▶ Запуск только веб-интерфейса..."
        echo ""
        echo "🌐 Веб-интерфейс будет доступен на:"
        echo "   http://localhost:5000 (логин: admin, пароль: admin123)"
        echo ""
        python3 run.py
        ;;
    4)
        echo "▶ Запуск бота на testnet..."
        python3 main.py --pairs 20 --testnet
        ;;
    5)
        echo "▶ Демонстрация возможностей..."
        python3 demo_mode.py
        ;;
    6)
        echo "▶ Полная проверка системы..."
        python3 check_all.py
        ;;
    7)
        echo "👋 До свидания!"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac
