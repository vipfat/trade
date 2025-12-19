"""
Flask веб-приложение для управления торговым ботом.
Предоставляет интерфейс для мониторинга логов, редактирования параметров,
контроля статуса и управления конфигурацией.
"""

import os
import json
import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, jsonify, 
    send_file, send_from_directory, session, redirect, url_for
)
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
CORS(app)
auth = HTTPBasicAuth()

# Пути
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / 'logs'
CONFIG_DIR = BASE_DIR / 'config'
BACKUP_DIR = CONFIG_DIR / 'backups'
ENV_FILE = BASE_DIR / '.env'

# Создание директорий
LOG_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ======================== AUTHENTICATION ========================

@auth.verify_password
def verify_password(username, password):
    """Проверка базовой аутентификации"""
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    if username == admin_user and password == admin_pass:
        return username
    return None


def require_auth(f):
    """Декоратор для защиты endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not auth.get_auth():
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ======================== CONFIGURATION MANAGEMENT ========================

class ConfigManager:
    """Управление конфигурацией бота"""
    
    DEFAULT_CONFIG = {
        'bot': {
            'pairs': 100,
            'interval': 300,
            'testnet': False,
            'leverage': 10,
            'max_positions': 5,
            'position_size_usdt': 100,
            'confidence_threshold': 0.65,
        },
        'strategies': {
            'lstm_weight': 0.60,
            'mean_reversion_weight': 0.25,
            'microstructure_weight': 0.15,
            'lstm_enabled': True,
            'mean_reversion_enabled': True,
            'microstructure_enabled': True,
        },
        'risk_management': {
            'take_profit_percent': 1.0,
            'stop_loss_percent': 2.0,
            'daily_loss_limit': 5.0,
            'daily_trades_per_symbol': 20,
            'max_drawdown_percent': 15.0,
        },
        'trading': {
            'timeframe': '5m',
            'min_volume_usdt': 1000000,
            'max_spread_percent': 0.05,
            'slippage_percent': 0.1,
        },
        'logging': {
            'level': 'INFO',
            'log_trades': True,
            'log_signals': True,
            'log_errors': True,
        }
    }
    
    @staticmethod
    def load_config():
        """Загрузить конфигурацию из файла"""
        config_file = CONFIG_DIR / 'bot_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки конфига: {e}")
        return ConfigManager.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config):
        """Сохранить конфигурацию в файл"""
        config_file = CONFIG_DIR / 'bot_config.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Конфигурация сохранена")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения конфига: {e}")
            return False
    
    @staticmethod
    def backup_config(config):
        """Создать резервную копию конфигурации"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f'bot_config_backup_{timestamp}.json'
        try:
            with open(backup_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Резервная копия создана: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
    
    @staticmethod
    def restore_defaults():
        """Восстановить конфигурацию по умолчанию"""
        ConfigManager.save_config(ConfigManager.DEFAULT_CONFIG.copy())
        logger.info("Конфигурация восстановлена к значениям по умолчанию")
        return ConfigManager.DEFAULT_CONFIG.copy()


class LogReader:
    """Чтение и обработка логов"""
    
    @staticmethod
    def get_log_file():
        """Получить основной файл логов"""
        return LOG_DIR / 'trading_bot.log'
    
    @staticmethod
    def read_logs(lines=100, tail=True):
        """Прочитать логи"""
        log_file = LogReader.get_log_file()
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                if tail:
                    # Последние N строк
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
                else:
                    return f.readlines()
        except Exception as e:
            logger.error(f"Ошибка чтения логов: {e}")
            return []
    
    @staticmethod
    def get_log_stats():
        """Получить статистику логов"""
        log_file = LogReader.get_log_file()
        if not log_file.exists():
            return {
                'total_lines': 0,
                'file_size': 0,
                'last_modified': None,
                'trades_count': 0,
                'errors_count': 0,
                'warnings_count': 0,
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            trades = sum(1 for line in lines if 'TRADE' in line or 'ORDER' in line)
            errors = sum(1 for line in lines if 'ERROR' in line)
            warnings = sum(1 for line in lines if 'WARNING' in line)
            
            return {
                'total_lines': len(lines),
                'file_size': log_file.stat().st_size,
                'file_size_mb': round(log_file.stat().st_size / (1024 * 1024), 2),
                'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
                'trades_count': trades,
                'errors_count': errors,
                'warnings_count': warnings,
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики логов: {e}")
            return {}
    
    @staticmethod
    def search_logs(keyword, lines=50):
        """Поиск по логам"""
        all_logs = LogReader.read_logs(lines=10000, tail=False)
        filtered = [log for log in all_logs if keyword.lower() in log.lower()]
        return filtered[-lines:] if len(filtered) > lines else filtered
    
    @staticmethod
    def get_recent_trades(count=20):
        """Получить последние сделки из логов"""
        logs = LogReader.read_logs(lines=5000, tail=False)
        trades = [log for log in logs if 'ORDER' in log or 'TRADE' in log]
        return trades[-count:]
    
    @staticmethod
    def clear_logs():
        """Очистить логи"""
        log_file = LogReader.get_log_file()
        try:
            open(log_file, 'w').close()
            logger.info("Логи очищены")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
            return False


# ======================== ENVIRONMENT MANAGEMENT ========================

class EnvManager:
    """Управление переменными окружения"""
    
    @staticmethod
    def load_env():
        """Загрузить переменные окружения"""
        if ENV_FILE.exists():
            try:
                env_vars = {}
                with open(ENV_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Скрывать чувствительные данные
                            if any(sensitive in key for sensitive in ['KEY', 'SECRET', 'PASSWORD']):
                                value = '***' if value else ''
                            env_vars[key] = value
                return env_vars
            except Exception as e:
                logger.error(f"Ошибка загрузки .env: {e}")
        return {}
    
    @staticmethod
    def save_env(env_dict):
        """Сохранить переменные окружения"""
        try:
            lines = []
            for key, value in env_dict.items():
                if value != '***':  # Не сохранять замаскированные значения
                    lines.append(f"{key}={value}\n")
            
            with open(ENV_FILE, 'w') as f:
                f.writelines(lines)
            logger.info(".env файл обновлен")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения .env: {e}")
            return False


# ======================== ROUTES - AUTHENTICATION ========================

@app.route('/api/login', methods=['POST'])
def login():
    """Вход в систему"""
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    admin_user = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    if username == admin_user and password == admin_pass:
        session['authenticated'] = True
        return jsonify({'success': True, 'message': 'Успешный вход'})
    
    return jsonify({'success': False, 'message': 'Неверные учетные данные'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """Выход из системы"""
    session.clear()
    return jsonify({'success': True})


@app.route('/api/is-authenticated')
def is_authenticated():
    """Проверить аутентификацию"""
    return jsonify({'authenticated': session.get('authenticated', False)})


# ======================== ROUTES - CONFIGURATION ========================

@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Получить текущую конфигурацию"""
    config = ConfigManager.load_config()
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
@require_auth
def update_config():
    """Обновить конфигурацию"""
    data = request.json
    config = ConfigManager.load_config()
    
    # Создать резервную копию перед обновлением
    ConfigManager.backup_config(config)
    
    # Обновить только переданные значения
    for section, values in data.items():
        if section in config and isinstance(values, dict):
            config[section].update(values)
    
    if ConfigManager.save_config(config):
        return jsonify({
            'success': True,
            'message': 'Конфигурация обновлена',
            'config': config
        })
    
    return jsonify({'success': False, 'message': 'Ошибка сохранения конфигурации'}), 500


@app.route('/api/config/defaults', methods=['POST'])
@require_auth
def reset_config_defaults():
    """Восстановить конфигурацию по умолчанию"""
    config = ConfigManager.restore_defaults()
    return jsonify({
        'success': True,
        'message': 'Конфигурация восстановлена к значениям по умолчанию',
        'config': config
    })


@app.route('/api/config/backups', methods=['GET'])
@require_auth
def get_backups():
    """Получить список резервных копий"""
    try:
        backups = sorted(
            [f.name for f in BACKUP_DIR.glob('*.json')],
            reverse=True
        )
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f"Ошибка получения списка резервных копий: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/restore/<backup_name>', methods=['POST'])
@require_auth
def restore_backup(backup_name):
    """Восстановить конфигурацию из резервной копии"""
    try:
        backup_file = BACKUP_DIR / backup_name
        if not backup_file.exists():
            return jsonify({'error': 'Резервная копия не найдена'}), 404
        
        with open(backup_file, 'r') as f:
            config = json.load(f)
        
        ConfigManager.save_config(config)
        return jsonify({
            'success': True,
            'message': f'Конфигурация восстановлена из {backup_name}',
            'config': config
        })
    except Exception as e:
        logger.error(f"Ошибка восстановления конфигурации: {e}")
        return jsonify({'error': str(e)}), 500


# ======================== ROUTES - LOGS ========================

@app.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    """Получить логи"""
    lines = request.args.get('lines', 100, type=int)
    logs = LogReader.read_logs(lines=lines)
    return jsonify({'logs': logs})


@app.route('/api/logs/stats', methods=['GET'])
@require_auth
def get_log_stats():
    """Получить статистику логов"""
    stats = LogReader.get_log_stats()
    return jsonify(stats)


@app.route('/api/logs/search', methods=['POST'])
@require_auth
def search_logs():
    """Поиск по логам"""
    data = request.json
    keyword = data.get('keyword', '')
    lines = data.get('lines', 50)
    
    if not keyword:
        return jsonify({'error': 'Keyword required'}), 400
    
    results = LogReader.search_logs(keyword, lines=lines)
    return jsonify({'results': results, 'count': len(results)})


@app.route('/api/logs/trades', methods=['GET'])
@require_auth
def get_recent_trades():
    """Получить последние сделки"""
    count = request.args.get('count', 20, type=int)
    trades = LogReader.get_recent_trades(count=count)
    return jsonify({'trades': trades})


@app.route('/api/logs/clear', methods=['POST'])
@require_auth
def clear_logs():
    """Очистить логи"""
    if LogReader.clear_logs():
        return jsonify({'success': True, 'message': 'Логи очищены'})
    return jsonify({'success': False, 'message': 'Ошибка очистки логов'}), 500


@app.route('/api/logs/download', methods=['GET'])
@require_auth
def download_logs():
    """Скачать логи в файл"""
    log_file = LogReader.get_log_file()
    if log_file.exists():
        return send_file(
            log_file,
            as_attachment=True,
            download_name=f'trading_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
    return jsonify({'error': 'Log file not found'}), 404


# ======================== ROUTES - ENVIRONMENT ========================

@app.route('/api/env', methods=['GET'])
@require_auth
def get_env():
    """Получить переменные окружения"""
    env_vars = EnvManager.load_env()
    return jsonify(env_vars)


@app.route('/api/env', methods=['POST'])
@require_auth
def update_env():
    """Обновить переменные окружения"""
    data = request.json
    if EnvManager.save_env(data):
        return jsonify({'success': True, 'message': '.env файл обновлен'})
    return jsonify({'success': False, 'message': 'Ошибка сохранения .env'}), 500


# ======================== ROUTES - STATUS & INFO ========================

@app.route('/api/status', methods=['GET'])
@require_auth
def get_status():
    """Получить статус бота"""
    config = ConfigManager.load_config()
    log_stats = LogReader.get_log_stats()
    
    return jsonify({
        'status': 'running',  # TODO: интегрировать с реальным статусом бота
        'config': config,
        'logs': log_stats,
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/system-info', methods=['GET'])
@require_auth
def get_system_info():
    """Получить информацию о системе"""
    import platform
    import psutil
    
    return jsonify({
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
        'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
    })


# ======================== ROUTES - STATIC & PAGES ========================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Дашборд"""
    return render_template('dashboard.html')


@app.route('/config')
def config_page():
    """Страница конфигурации"""
    return render_template('config.html')


@app.route('/logs-view')
def logs_page():
    """Страница логов"""
    return render_template('logs.html')


@app.route('/env-config')
def env_config_page():
    """Страница управления переменными окружения"""
    return render_template('env.html')


# ======================== ERROR HANDLERS ========================

@app.errorhandler(404)
def not_found(error):
    """Обработка 404"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка 500"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ======================== CLI RUNNER ========================

if __name__ == '__main__':
    import sys
    
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║          🌐 Trading Bot Web Interface                      ║
    ╠════════════════════════════════════════════════════════════╣
    ║ Адрес:    http://localhost:{port:<45}║
    ║ API:      http://localhost:{port}/api/                    ║
    ║ Debug:    {str(debug):<48}║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
