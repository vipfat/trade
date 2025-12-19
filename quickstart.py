#!/usr/bin/env python3
"""
Скрипт для быстрого старта торгового бота
Спрашивает несколько вопросов и запускает бот с правильными параметрами
"""

import os
import sys
import subprocess
from pathlib import Path

def clear_screen():
    """Очистить экран"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Печать заголовка"""
    print("\n" + "="*60)
    print("🤖 Trading Bot - Быстрый старт")
    print("="*60 + "\n")

def check_env():
    """Проверить .env файл"""
    if not Path('.env').exists():
        print("❌ Файл .env не найден!")
        print("Создайте его:")
        print("  copy .env.example .env  (Windows)")
        print("  cp .env.example .env    (Linux/Mac)")
        print("\nЗатем добавьте API ключи от Bybit")
        sys.exit(1)

def check_models():
    """Проверить есть ли обученная модель"""
    if Path('lstm_model.h5').exists():
        print("✅ Найдена обученная модель LSTM")
        return True
    else:
        print("⚠️ Обученная модель не найдена")
        print("Бот обучит её при первом запуске (займет 3-5 минут)")
        return False

def main():
    clear_screen()
    print_header()
    
    # Проверки
    check_env()
    has_model = check_models()
    
    print("\n" + "="*60)
    print("ВЫБЕРИТЕ ЧТО ХОТИТЕ СДЕЛАТЬ:")
    print("="*60)
    print("""
1️⃣  Запустить веб-интерфейс (http://localhost:5000)
2️⃣  Запустить бота на TESTNET (рекомендуется)
3️⃣  Запустить бота на MAINNET (реальные деньги)
4️⃣  Протестировать стратегию (бэктест)
5️⃣  Обучить LSTM модель
6️⃣  Запустить оба: веб-интерфейс + бот на testnet
0️⃣  Выход

""")
    
    choice = input("Выберите опцию (0-6): ").strip()
    
    if choice == '1':
        print("\n🌐 Запускаю веб-интерфейс...")
        print("Откройте http://localhost:5000 и введите: admin / admin123\n")
        os.system("python run.py")
    
    elif choice == '2':
        print("\n🤖 Запускаю бота на TESTNET...")
        print("Это безопасно для тестирования\n")
        
        pairs = input("Сколько пар торговать? (по умолчанию 20): ").strip() or "20"
        
        config_choice = input("""
Выберите конфигурацию:
  1 - Conservative (минимальный риск)
  2 - Balanced (рекомендуется)
  3 - Aggressive (максимум профита)
  (по умолчанию 2): """).strip() or "2"
        
        configs = {"1": "conservative", "2": "balanced", "3": "aggressive"}
        config = configs.get(config_choice, "balanced")
        
        cmd = f"python main.py --pairs {pairs} --config {config} --testnet --verbose"
        print(f"\n📝 Команда: {cmd}\n")
        os.system(cmd)
    
    elif choice == '3':
        print("\n⚠️ ВНИМАНИЕ! Вы запускаете бота на REAL MONEY!")
        print("Убедитесь что:")
        print("  ✓ Вы протестировали на testnet минимум 3 дня")
        print("  ✓ Вы понимаете что можете потерять деньги")
        print("  ✓ Вы используете CONSERVATIVE конфигурацию")
        
        confirm = input("\nВы уверены? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Отменено")
            return
        
        pairs = input("Сколько пар торговать? (по умолчанию 50): ").strip() or "50"
        
        cmd = f"python main.py --pairs {pairs} --config conservative --verbose"
        print(f"\n📝 Команда: {cmd}\n")
        print("💰 БОТА ЗАПУЩЕН НА РЕАЛЬНОМ СЧЕТЕ!")
        print("Следи за Dashboard каждый час!\n")
        os.system(cmd)
    
    elif choice == '4':
        print("\n🧪 Запускаю бэктестирование...")
        
        days = input("Сколько дней тестировать? (по умолчанию 30): ").strip() or "30"
        
        config_choice = input("""
Выберите конфигурацию:
  1 - Conservative
  2 - Balanced
  3 - Aggressive
  (по умолчанию 2): """).strip() or "2"
        
        configs = {"1": "conservative", "2": "balanced", "3": "aggressive"}
        config = configs.get(config_choice, "balanced")
        
        cmd = f"python backtest.py --days {days} --config {config}"
        print(f"\n📝 Команда: {cmd}\n")
        os.system(cmd)
    
    elif choice == '5':
        print("\n🧠 Обучаю LSTM модель...")
        print("Это займет 3-5 минут\n")
        
        pairs = input("Сколько пар использовать? (по умолчанию 10): ").strip() or "10"
        lookback = input("Сколько свечей? (по умолчанию 100): ").strip() or "100"
        
        cmd = f"python main.py --pairs {pairs} --testnet --retrain --lookback {lookback}"
        print(f"\n📝 Команда: {cmd}\n")
        os.system(cmd)
    
    elif choice == '6':
        print("\n🚀 Запускаю веб-интерфейс + бот на testnet...")
        print("\nОткройте в браузере: http://localhost:5000")
        print("(логин: admin, пароль: admin123)\n")
        print("Запускаю два процесса...")
        print("Нажмите Ctrl+C в любом терминале для остановки\n")
        
        # Запустить веб интерфейс в фоне
        if os.name == 'nt':
            os.system("start python run.py")
        else:
            os.system("python run.py &")
        
        # Запустить бот
        pairs = input("Сколько пар торговать? (по умолчанию 20): ").strip() or "20"
        cmd = f"python main.py --pairs {pairs} --config balanced --testnet --verbose"
        os.system(cmd)
    
    elif choice == '0':
        print("До свидания! 👋")
        sys.exit(0)
    
    else:
        print("❌ Неправильный выбор")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
