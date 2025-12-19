#!/usr/bin/env python3
"""
Скрипт для инициализации и первой настройки торгового бота
"""

import os
import sys
from src.api.bybit_client import BybitClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def check_api_credentials():
    """Проверить наличие API credentials"""
    print("\n" + "="*60)
    print("📌 ПРОВЕРКА API CREDENTIALS")
    print("="*60)
    
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or api_key == 'your_api_key_here':
        print("❌ BYBIT_API_KEY не установлен в .env")
        return False
    
    if not api_secret or api_secret == 'your_api_secret_here':
        print("❌ BYBIT_API_SECRET не установлен в .env")
        return False
    
    print("✅ API Credentials найдены")
    return True

def test_bybit_connection():
    """Протестировать подключение к Bybit"""
    print("\n" + "="*60)
    print("🌐 ТЕСТ ПОДКЛЮЧЕНИЯ К BYBIT")
    print("="*60)
    
    try:
        bybit = BybitClient()
        
        # Пробуем получить баланс
        balance = bybit.get_balance()
        if balance:
            print("✅ Подключение успешно!")
            print(f"   Доступный баланс USDT: {balance.get('USDT', {}).get('available_balance', 'N/A')}")
            return True
        else:
            print("❌ Не удалось получить баланс")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def check_trading_pairs():
    """Проверить доступные торговые пары"""
    print("\n" + "="*60)
    print("📊 ДОСТУПНЫЕ ТОРГОВЫЕ ПАРЫ")
    print("="*60)
    
    try:
        bybit = BybitClient()
        pairs = bybit.get_trading_pairs(min_volume_usdt=100000)
        
        if pairs:
            print(f"✅ Найдено {len(pairs)} пар с объемом > 100k USDT")
            print("\nТоп 10 пар по объему:")
            for i, pair in enumerate(pairs[:10], 1):
                volume = pair['volume'] / 1e6  # Конвертируем в миллионы
                print(f"   {i}. {pair['symbol']}: ${volume:.2f}M")
            
            # Показываем пары для торговли (6-15)
            print("\nПары для торговли (позиции 6-15):")
            for i, pair in enumerate(pairs[5:15], 6):
                volume = pair['volume'] / 1e6
                print(f"   {i}. {pair['symbol']}: ${volume:.2f}M")
            
            return True
        else:
            print("❌ Не удалось получить список пар")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка получения пар: {e}")
        return False

def test_model_training():
    """Тест обучения LSTM модели"""
    print("\n" + "="*60)
    print("🤖 ТЕСТ ОБУЧЕНИЯ LSTM МОДЕЛИ")
    print("="*60)
    
    try:
        from src.models.lstm_model import LSTMPricePredictor
        import pandas as pd
        
        bybit = BybitClient()
        lstm = LSTMPricePredictor()
        
        print("Получаю исторические данные для обучения...")
        df = bybit.get_klines('BTCUSDT', interval='5', limit=500)
        
        if df is None or len(df) < 100:
            print("❌ Недостаточно данных для обучения")
            return False
        
        print(f"✅ Получено {len(df)} свечей")
        print("Обучаю модель (это может занять 1-2 минуты)...")
        
        if lstm.train(df, epochs=5, batch_size=32):
            print("✅ Модель успешно обучена!")
            
            # Пробуем предсказание
            prediction = lstm.predict(df)
            if prediction:
                print(f"   Пример предсказания: {prediction}")
            
            # Сохраняем модель
            lstm.save_model('lstm_model_test')
            print("✅ Модель сохранена в models_saved/")
            return True
        else:
            print("❌ Ошибка обучения модели")
            return False
    
    except Exception as e:
        print(f"❌ Ошибка при тесте модели: {e}")
        return False

def show_configuration():
    """Показать текущую конфигурацию"""
    print("\n" + "="*60)
    print("⚙️  ТЕКУЩАЯ КОНФИГУРАЦИЯ")
    print("="*60)
    
    config = {
        'LEVERAGE': os.getenv('LEVERAGE', '10'),
        'POSITION_SIZE_USDT': os.getenv('POSITION_SIZE_USDT', '100'),
        'MAX_POSITIONS': os.getenv('MAX_POSITIONS', '5'),
        'MAX_LOSS_PERCENT': os.getenv('MAX_LOSS_PERCENT', '2.0'),
        'CONFIDENCE_THRESHOLD': os.getenv('CONFIDENCE_THRESHOLD', '0.65'),
        'BYBIT_TESTNET': os.getenv('BYBIT_TESTNET', 'False')
    }
    
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    if config['BYBIT_TESTNET'].lower() == 'true':
        print("\n⚠️  РЕЖИМ TESTNET - это безопасно для тестирования!")
    else:
        print("\n🚨 РЕЖИМ РЕАЛЬНОЙ ТОРГОВЛИ - используйте осторожно!")

def show_next_steps():
    """Показать следующие шаги"""
    print("\n" + "="*60)
    print("📋 СЛЕДУЮЩИЕ ШАГИ")
    print("="*60)
    
    print("""
1️⃣  Отредактируйте .env файл:
   nano .env
   
2️⃣  Начните с TESTNET:
   python main.py --pairs 10 --interval 300 --testnet
   
3️⃣  Мониторьте логи:
   tail -f logs/trading_bot.log
   
4️⃣  Если всё работает хорошо, перейдите на реальный аккаунт:
   python main.py --pairs 50 --interval 300
   
5️⃣  Начните с маленькими позициями (10-50 USDT)!

6️⃣  Мониторьте первые 24 часа!
   """)

def main():
    """Запустить все проверки"""
    print("\n" + "="*80)
    print(" 🚀 ИНИЦИАЛИЗАЦИЯ ГИБРИДНОГО ТОРГОВОГО БОТА")
    print("="*80)
    
    # Проверяем .env файл
    if not os.path.exists('.env'):
        print("\n❌ Файл .env не найден!")
        print("   Создайте его: cp .env.example .env")
        print("   Отредактируйте с вашими API ключами")
        sys.exit(1)
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Запускаем проверки
    checks = [
        ("API Credentials", check_api_credentials),
        ("Bybit Connection", test_bybit_connection),
        ("Trading Pairs", check_trading_pairs),
        ("LSTM Model", test_model_training),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Ошибка при выполнении проверки '{name}': {e}")
            results[name] = False
    
    # Показываем конфигурацию
    show_configuration()
    
    # Резюме
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРОК")
    print("="*60)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! БОТ ГОТОВ К РАБОТЕ")
        show_next_steps()
    else:
        print("\n❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("   Пожалуйста, исправьте ошибки и попробуйте снова")
        sys.exit(1)

if __name__ == '__main__':
    main()
