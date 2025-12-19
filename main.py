#!/usr/bin/env python3
"""
Главный скрипт для запуска гибридного торгового бота
Использует LSTM + Mean Reversion + Microstructure анализ
"""

import argparse
import time
import signal
import sys
from datetime import datetime
from src.bot.hybrid_bot import HybridTradingBot
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class BotRunner:
    """Запускатель бота с контролем цикла"""
    
    def __init__(self, trading_pairs_count=100):
        self.bot = HybridTradingBot()
        self.trading_pairs_count = trading_pairs_count
        self.trading_pairs = []
        self.is_running = True
        self.iteration_count = 0
        
        # Обработка сигналов для красивого завершения
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Обработчик для завершения бота"""
        logger.info("Получен сигнал завершения, закрываю позиции...")
        self.is_running = False
    
    def initialize(self):
        """Инициализировать бота (получить пары, обучить модель)"""
        logger.info("=== Инициализация бота ===")
        
        # Получаем топ пары
        self.trading_pairs = self.bot.get_top_trading_pairs(
            num_pairs=self.trading_pairs_count,
            skip_top_n=5
        )
        
        if not self.trading_pairs:
            logger.error("Не удалось получить торговые пары!")
            return False
        
        logger.info(f"Будем торговать {len(self.trading_pairs)} парами")
        logger.info(f"Первые 10 пар: {self.trading_pairs[:10]}")
        
        # Пробуем загрузить обученную модель
        try:
            if self.bot.lstm.load_model('lstm_model'):
                logger.info("Загружена ранее обученная модель LSTM")
            else:
                logger.info("Загруженная модель не найдена, обучу на исторических данных")
                self._train_initial_model()
        except Exception as e:
            logger.warning(f"Ошибка загрузки модели: {e}, обучу с нуля")
            self._train_initial_model()
        
        return True
    
    def _train_initial_model(self):
        """Обучить модель на исторических данных"""
        logger.info("Получаю исторические данные для обучения...")
        
        try:
            import pandas as pd
            
            # Используем несколько пар для обучения
            sample_pairs = self.trading_pairs[10:15]
            combined_df = pd.DataFrame()
            
            for symbol in sample_pairs:
                logger.info(f"Получаю данные для {symbol}...")
                df = self.bot.bybit.get_klines(symbol, interval="5", limit=500)
                if df is not None and len(df) > 0:
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
                time.sleep(0.5)  # Избегаем rate limiting
            
            if len(combined_df) > self.bot.config['lookback_period']:
                logger.info(f"Обучаю модель на {len(combined_df)} свечах...")
                self.bot.lstm.train(combined_df, epochs=20, batch_size=32)
                self.bot.lstm.save_model('lstm_model')
                logger.info("Модель успешно обучена!")
            else:
                logger.warning("Недостаточно данных для обучения модели")
        
        except Exception as e:
            logger.error(f"Ошибка обучения модели: {e}")
    
    def run(self, interval_seconds=300):
        """
        Запустить основной цикл бота
        
        Args:
            interval_seconds: Интервал между итерациями (300 = 5 минут)
        """
        if not self.initialize():
            logger.error("Инициализация не удалась!")
            return
        
        logger.info(f"=== Бот запущен ===")
        logger.info(f"Интервал между итерациями: {interval_seconds} сек")
        logger.info(f"Время начала: {datetime.now()}")
        logger.info("")
        
        while self.is_running:
            try:
                self.iteration_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"ИТЕРАЦИЯ #{self.iteration_count} - {datetime.now()}")
                logger.info(f"{'='*60}")
                
                # Запускаем торговлю
                self.bot.run_iteration(self.trading_pairs)
                
                # Выводим текущую статистику
                self._print_stats()
                
                # Ждем перед следующей итерацией
                logger.info(f"Жду {interval_seconds} сек до следующей итерации...")
                time.sleep(interval_seconds)
            
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(30)  # Жду перед повторной попыткой
        
        logger.info("\n=== Бот остановлен ===")
    
    def _print_stats(self):
        """Вывести статистику бота"""
        total_trades = sum(self.bot.trades_today.values())
        total_positions = len(self.bot.positions)
        open_positions = sum(1 for p in self.bot.positions.values() if p['status'] == 'open')
        
        logger.info(f"\nТекущая статистика:")
        logger.info(f"  Всего торговль сегодня: {total_trades}")
        logger.info(f"  Всего позиций: {total_positions}")
        logger.info(f"  Открытых позиций: {open_positions}")
        
        # Выводим топ пары по количеству торговель
        top_symbols = sorted(
            self.bot.trades_today.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        if top_symbols:
            logger.info(f"  Топ пары по торговлям:")
            for symbol, count in top_symbols:
                logger.info(f"    - {symbol}: {count} торговль")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Гибридный торговый бот для Bybit')
    parser.add_argument('--pairs', type=int, default=100, help='Количество торговых пар (по умолчанию 100)')
    parser.add_argument('--interval', type=int, default=300, help='Интервал между итерациями в секундах (по умолчанию 300)')
    parser.add_argument('--testnet', action='store_true', help='Использовать testnet вместо mainnet')
    
    args = parser.parse_args()
    
    # Перезаписываем переменные окружения если нужно
    if args.testnet:
        import os
        os.environ['BYBIT_TESTNET'] = 'True'
    
    # Запускаем бот
    runner = BotRunner(trading_pairs_count=args.pairs)
    runner.run(interval_seconds=args.interval)


if __name__ == '__main__':
    main()
