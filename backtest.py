#!/usr/bin/env python3
"""
Backtesting скрипт для оценки стратегии на исторических данных
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.api.bybit_client import BybitClient
from src.models.lstm_model import LSTMPricePredictor
from src.strategies.mean_reversion import MeanReversionAnalyzer
from src.utils.logger import setup_logger
import time

logger = setup_logger(__name__)

class BacktestEngine:
    """Движок для бэктестирования стратегии"""
    
    def __init__(self, initial_balance=10000):
        """
        Args:
            initial_balance: Начальный баланс в USDT
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        
        self.trades = []
        self.positions = []
        self.pnl_history = []
        
        self.bybit = BybitClient()
        self.lstm = LSTMPricePredictor()
        self.mean_reversion = MeanReversionAnalyzer()
    
    def backtest(self, symbol, days=30, interval='5'):
        """
        Запустить бэктест на исторических данных
        
        Args:
            symbol: Торговая пара
            days: Количество дней истории
            interval: Таймфрейм свечей
        """
        logger.info(f"=== Бэктест {symbol} на {days} дней ===")
        
        # Получаем исторические данные
        limit = days * 24 * 60 // int(interval)  # Количество свечей
        df = self.bybit.get_klines(symbol, interval=interval, limit=limit)
        
        if df is None or len(df) < 100:
            logger.error(f"Не удалось получить данные для {symbol}")
            return None
        
        logger.info(f"Получено {len(df)} свечей")
        
        # Попробуем загрузить или обучить модель
        if not self.lstm.load_model('lstm_model'):
            logger.info("Обучаю модель на полученных данных...")
            self.lstm.train(df.iloc[:500], epochs=20, batch_size=32)
        
        # Симулируем торговлю
        winning_trades = 0
        losing_trades = 0
        total_pnl = 0
        
        for i in range(100, len(df) - 1):
            # Окно данных для анализа
            window = df.iloc[i-100:i+1]
            
            # Получаем сигналы
            ml_signal = self.lstm.predict(window, return_confidence=True)
            if ml_signal is None:
                continue
            
            mr_result = self.mean_reversion.analyze(window)
            
            # Объединяем сигналы
            ml_confidence = ml_signal['confidence']
            mr_confidence = mr_result['confidence']
            
            buy_confidence = (ml_signal['direction'] == 1) * ml_confidence * 0.6 + \
                            (mr_result['signal'] == 'BUY') * mr_confidence * 0.4
            
            sell_confidence = (ml_signal['direction'] == 0) * ml_confidence * 0.6 + \
                             (mr_result['signal'] == 'SELL') * mr_confidence * 0.4
            
            # Определяем сигнал
            if buy_confidence > sell_confidence and buy_confidence > 0.65:
                signal = 'BUY'
                confidence = buy_confidence
            elif sell_confidence > buy_confidence and sell_confidence > 0.65:
                signal = 'SELL'
                confidence = sell_confidence
            else:
                continue
            
            # Экспортируем сделку (очень упрощенно)
            entry_price = window['close'].iloc[-1]
            exit_price = df['close'].iloc[i+1]  # Выходим на следующей свече
            
            if signal == 'BUY':
                pnl = (exit_price - entry_price) * 1  # Размер позиции = 1 контракт
            else:
                pnl = (entry_price - exit_price) * 1
            
            pnl_percent = (pnl / entry_price) * 100
            
            if pnl > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            
            total_pnl += pnl
            
            self.trades.append({
                'datetime': window.index[-1],
                'symbol': symbol,
                'signal': signal,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'confidence': confidence
            })
            
            self.pnl_history.append(total_pnl)
        
        # Выводим результаты
        return self._print_results(winning_trades, losing_trades, total_pnl)
    
    def _print_results(self, winning_trades, losing_trades, total_pnl):
        """Вывести результаты бэктеста"""
        total_trades = winning_trades + losing_trades
        
        if total_trades == 0:
            logger.info("Нет сделок для анализа")
            return None
        
        win_rate = (winning_trades / total_trades) * 100
        avg_win = total_pnl / max(winning_trades, 1) if winning_trades > 0 else 0
        
        logger.info("\n=== РЕЗУЛЬТАТЫ БЭКТЕСТА ===")
        logger.info(f"Всего сделок: {total_trades}")
        logger.info(f"  Прибыльных: {winning_trades}")
        logger.info(f"  Убыточных: {losing_trades}")
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Общий P&L: {total_pnl:.2f} USDT")
        logger.info(f"Return on Investment: {(total_pnl / self.initial_balance) * 100:.2f}%")
        logger.info(f"Средний профит на сделку: {avg_win:.2f} USDT")
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'roi': (total_pnl / self.initial_balance) * 100
        }


def main():
    """Запустить бэктест"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backtester для торгового бота')
    parser.add_argument('--symbol', default='BTCUSDT', help='Торговая пара (по умолчанию BTCUSDT)')
    parser.add_argument('--days', type=int, default=30, help='Количество дней для бэктеста')
    
    args = parser.parse_args()
    
    engine = BacktestEngine(initial_balance=10000)
    engine.backtest(args.symbol, days=args.days)


if __name__ == '__main__':
    main()
