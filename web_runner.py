#!/usr/bin/env python3
"""
Запуск веб-интерфейса управления торговым ботом.
Web Interface Runner for Trading Bot Control Panel.

Использование:
    python web_runner.py              # Запуск с default параметрами
    python web_runner.py --port 8080  # Запуск на port 8080
    python web_runner.py --debug      # Запуск с debug режимом
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description='Trading Bot Web Interface Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
    python web_runner.py                    # Базовый запуск
    python web_runner.py --port 8080        # Кастомный port
    python web_runner.py --debug            # Debug режим
    python web_runner.py --host 0.0.0.0     # Доступно со всех IP
        """
    )
    
    parser.add_argument('--port', type=int, default=5000,
                        help='Port для веб-интерфейса (default: 5000)')
    parser.add_argument('--host', default='localhost',
                        help='Host для binding (default: localhost)')
    parser.add_argument('--debug', action='store_true',
                        help='Запуск в debug режиме')
    parser.add_argument('--reload', action='store_true',
                        help='Auto-reload при изменении файлов')
    
    args = parser.parse_args()
    
    # Проверка зависимостей
    try:
        import flask
        import flask_cors
        import flask_httpauth
    except ImportError:
        print("❌ Зависимости не установлены!")
        print("\nУстановите их командой:")
        print(f"  pip install -r {Path(__file__).parent / 'requirements.txt'}")
        sys.exit(1)
    
    # Проверка .env файла
    env_file = Path(__file__).parent.parent / '.env'
    if not env_file.exists():
        print("⚠️  Файл .env не найден!")
        print(f"   Создайте его из .env.example:")
        print(f"   cp .env.example .env")
        print()
        print("   Затем добавьте ваши API ключи от Bybit:")
        print("   BYBIT_API_KEY=your_key")
        print("   BYBIT_API_SECRET=your_secret")
        sys.exit(1)
    
    # Вывод информации
    print(f"""
╔════════════════════════════════════════════════════════════╗
║     🌐 Trading Bot Web Interface                           ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Запуск веб-интерфейса:                                   ║
║  ├─ Host:     http://{args.host}:{args.port:<42}
║  ├─ Debug:    {str(args.debug):<45}
║  ├─ Reload:   {str(args.reload):<45}
║  └─ Default Admin: admin / admin123                        ║
║                                                            ║
║  Используйте Ctrl+C для остановки                         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Запуск Flask приложения
    from app import app
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.reload
        )
    except KeyboardInterrupt:
        print("\n\n✓ Веб-интерфейс остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
