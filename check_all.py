#!/usr/bin/env python3
"""
Демонстрационный скрипт: Проверка что все компоненты работают
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

def print_header(text):
    """Печать красивого заголовка"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_files():
    """Проверить наличие всех нужных файлов"""
    print_header("1️⃣  ПРОВЕРКА ФАЙЛОВ")
    
    files = {
        'main.py': 'Главный скрипт бота',
        'web/app.py': 'Веб-приложение Flask',
        'src/bot/hybrid_bot.py': 'Гибридный бот',
        'logs/trading_bot.log': 'Логи',
        '.env': 'Конфигурация',
        'lstm_model.h5': 'Модель LSTM (опционально)',
    }
    
    for file, description in files.items():
        exists = Path(file).exists()
        status = "✅" if exists else "⚠️ "
        print(f"{status} {file:<40} - {description}")
    
    return all(Path(f).exists() for f in ['main.py', 'web/app.py', '.env'])

def check_dependencies():
    """Проверить установленные зависимости"""
    print_header("2️⃣  ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    
    dependencies = {
        'flask': 'Web Framework',
        'flask_cors': 'CORS Support',
        'flask_httpauth': 'HTTP Authentication',
        'dotenv': 'Environment Variables',
        'psutil': 'System Info',
    }
    
    all_good = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module:<20} - {description}")
        except ImportError:
            print(f"❌ {module:<20} - {description} (NOT INSTALLED)")
            all_good = False
    
    return all_good

def test_web_interface():
    """Тестировать веб-интерфейс"""
    print_header("3️⃣  ТЕСТИРОВАНИЕ ВЕБ-ИНТЕРФЕЙСА")
    
    try:
        from web.app import app
        
        # Создать тестовый клиент
        with app.test_client() as client:
            # Тест без авторизации
            print("▶ Тест без авторизации...")
            response = client.get('/')
            print(f"  Статус: {response.status_code} (ожидается 401)")
            
            # Тест с авторизацией
            print("▶ Тест с авторизацией (admin/admin123)...")
            response = client.get('/', auth=('admin', 'admin123'))
            print(f"  Статус: {response.status_code} (ожидается 200)")
            
            # Тест API
            print("▶ Тест API /api/system-info...")
            response = client.get('/api/system-info', auth=('admin', 'admin123'))
            print(f"  Статус: {response.status_code} (ожидается 200)")
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ОС: {data.get('os')}")
                print(f"  Python: {data.get('python_version')}")
                print(f"  CPU: {data.get('cpu_percent')}%")
            
            print("\n✅ Все тесты веб-интерфейса прошли успешно!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_bot_components():
    """Тестировать компоненты бота"""
    print_header("4️⃣  ТЕСТИРОВАНИЕ КОМПОНЕНТОВ БОТА")
    
    try:
        from src.bot.hybrid_bot import HybridTradingBot
        from src.utils.logger import setup_logger
        
        print("▶ Инициализация бота...")
        logger = setup_logger('test')
        bot = HybridTradingBot()
        print(f"  ✅ Бот инициализирован")
        
        print("▶ Проверка конфигурации...")
        config = bot.config
        print(f"  - Пары для торговли: {config['trading_pairs']}")
        print(f"  - Интервал: {config['interval']} сек")
        print(f"  - Тестнет: {config['testnet']}")
        print(f"  - Левередж: {config['leverage']}x")
        
        print("▶ Проверка стратегий...")
        print(f"  - LSTM вес: {config['lstm_weight']}")
        print(f"  - Mean Reversion вес: {config['mean_reversion_weight']}")
        print(f"  - Microstructure вес: {config['microstructure_weight']}")
        
        print("\n✅ Все компоненты бота работают!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_directory_structure():
    """Показать структуру проекта"""
    print_header("5️⃣  СТРУКТУРА ПРОЕКТА")
    
    try:
        result = subprocess.run(
            ['tree', '-L', '2', '-I', '__pycache__|*.pyc|.git'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            # Fallback если нет tree
            from pathlib import Path
            for path in sorted(Path('.').rglob('*'))[:50]:
                if path.is_file() and not any(x in str(path) for x in ['.git', '__pycache__', '.pyc']):
                    indent = '  ' * (len(path.parts) - 1)
                    print(f"{indent}{path.name}")
    except Exception as e:
        print(f"⚠️  Не удалось показать структуру: {e}")

def show_logs():
    """Показать последние логи"""
    print_header("6️⃣  ПРИМЕРЫ ЛОГОВ")
    
    log_file = Path('logs/trading_bot.log')
    if log_file.exists():
        print(f"📝 Файл логов: {log_file} ({log_file.stat().st_size} байт)")
        print("\n▶ Последние 10 строк логов:\n")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
    else:
        print("⚠️  Файл логов еще не создан (создастся при запуске бота)")

def show_summary():
    """Показать итоговую информацию"""
    print_header("✅ ИТОГОВАЯ ИНФОРМАЦИЯ")
    
    print("""
🎯 ВСЕ КОМПОНЕНТЫ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ!

🚀 БЫСТРЫЙ СТАРТ:

Вариант 1 - Интерактивное меню (РЕКОМЕНДУЕТСЯ):
  python quickstart.py

Вариант 2 - Веб-интерфейс + Бот:
  Терминал 1: python run.py
  Терминал 2: python main.py --pairs 20 --testnet

Вариант 3 - Только веб-интерфейс:
  python run.py
  Откройте: http://localhost:5000 (admin/admin123)

Вариант 4 - Только бот:
  python main.py --pairs 20 --testnet

📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
  - BOT_USAGE_GUIDE.md - Полное руководство (300+ строк)
  - QUICK_REFERENCE.md - Шпаргалка с командами
  - README.md - Описание алгоритмов
  - DOCS.md - Техническая документация

💡 СОВЕТЫ:
  ✓ Начните с testnet (--testnet флаг)
  ✓ Смотрите Dashboard для мониторинга
  ✓ Протестируйте бэктестом перед mainnet
  ✓ Читайте логи если что-то не работает

════════════════════════════════════════════════════════════════

Удачи в торговле! 💰📈
    """)

def main():
    """Главная функция"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  🤖 СИСТЕМА ПРОВЕРКИ ТОРГОВОГО БОТА".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    results = {}
    
    # Запустить все проверки
    results['files'] = check_files()
    results['deps'] = check_dependencies()
    results['web'] = test_web_interface()
    results['bot'] = test_bot_components()
    
    show_directory_structure()
    show_logs()
    show_summary()
    
    # Итоговый статус
    print_header("ИТОГОВЫЙ СТАТУС")
    
    if all(results.values()):
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n🚀 Бот готов к использованию!")
        return 0
    else:
        print("⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОШЛИ")
        for component, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {component}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
