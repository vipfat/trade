#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🌐 Trading Bot Web Interface - Простой запуск
Работает на Windows, Mac и Linux
"""

import sys
import os

def check_dependencies():
    """Проверить все зависимости"""
    print("\n📦 Проверка зависимостей...")
    
    required = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'flask_httpauth': 'Flask-HTTPAuth',
        'dotenv': 'python-dotenv',
        'psutil': 'psutil'
    }
    
    missing = []
    for module, package_name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name}")
            missing.append(package_name)
    
    if missing:
        print(f"\n❌ Отсутствуют пакеты: {', '.join(missing)}")
        print("\nУстановите их командой:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✓ Все зависимости установлены\n")
    return True

def check_env():
    """Проверить .env файл"""
    print("🔑 Проверка конфигурации...")
    
    if not os.path.exists('.env'):
        print("⚠️  Файл .env не найден\n")
        print("Создайте его из .env.example:")
        print("  copy .env.example .env  (Windows)")
        print("  cp .env.example .env    (Linux/Mac)")
        print("\nТатем отредактируйте .env и добавьте API ключи от Bybit")
        return False
    
    print("✓ Файл .env найден\n")
    return True

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🌐 Trading Bot Web Interface Launcher")
    print("="*60)
    
    # Проверки
    if not check_dependencies():
        sys.exit(1)
    
    if not check_env():
        sys.exit(1)
    
    # Запуск Flask
    print("🚀 Запуск веб-интерфейса...\n")
    print("-" * 60)
    
    try:
        from web.app import app
        
        port = os.getenv('WEB_PORT', '5000')
        host = '127.0.0.1'
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        print(f"\n✅ Веб-интерфейс запущен!")
        print(f"   🌐 Откройте: http://{host}:{port}")
        print(f"   📝 Логин: {username}")
        print(f"   🔐 Пароль: {password}")
        print(f"\n   Нажмите Ctrl+C для остановки\n")
        print("-" * 60 + "\n")
        
        app.run(host=host, port=int(port), debug=debug)
        
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        print("\nДополнительная информация:")
        print(f"  Python версия: {sys.version}")
        print(f"  Текущая папка: {os.getcwd()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
