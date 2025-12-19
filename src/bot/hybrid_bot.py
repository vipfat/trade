import asyncio
import time
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

from src.api.bybit_client import BybitClient
from src.models.lstm_model import LSTMPricePredictor
from src.strategies.mean_reversion import MeanReversionAnalyzer
from src.strategies.microstructure import MicrostructureAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class HybridTradingBot:
    """
    Гибридный торговый бот с максимумом сделок и стабильностью
    
    Использует:
    - 60% LSTM (ML предсказание)
    - 25% Mean Reversion (фильтр шума)
    - 15% Microstructure (анализ ордеров)
    """
    
    def __init__(self, config=None):
        """
        Args:
            config: dict с параметрами бота
        """
        self.config = config or self._default_config()
        
        # API клиент
        self.bybit = BybitClient()
        
        # Стратегии
        self.lstm = LSTMPricePredictor(lookback_period=self.config['lookback_period'])
        self.mean_reversion = MeanReversionAnalyzer()
        self.microstructure = MicrostructureAnalyzer()
        
        # Отслеживание позиций и сделок
        self.positions = {}  # {symbol: position_info}
        self.trades_today = defaultdict(int)  # {symbol: количество сделок за день}
        self.last_trade_time = {}  # {symbol: последнее время торговли}
        
        # Время последнего переобучения модели
        self.last_retrain_time = None
        
        logger.info("Гибридный торговый бот инициализирован")
    
    @staticmethod
    def _default_config():
        """Конфигурация по умолчанию"""
        return {
            'lookback_period': 100,
            'position_size_usdt': float(os.getenv('POSITION_SIZE_USDT', 100)),
            'max_positions': int(os.getenv('MAX_POSITIONS', 5)),
            'leverage': int(os.getenv('LEVERAGE', 10)),
            'max_loss_percent': float(os.getenv('MAX_LOSS_PERCENT', 2.0)),
            'confidence_threshold': float(os.getenv('CONFIDENCE_THRESHOLD', 0.65)),
            'ml_weight': 0.60,
            'mr_weight': 0.25,
            'ms_weight': 0.15,
            'max_trades_per_symbol_per_day': 20,
            'min_time_between_trades_seconds': 30
        }
    
    def get_top_trading_pairs(self, num_pairs=100, skip_top_n=5):
        """
        Получить топ торговых пар (пропускаем первые skip_top_n)
        
        Args:
            num_pairs: Количество пар для торговли
            skip_top_n: Пропустить первые N пар по объему
        
        Returns:
            list с символами пар
        """
        logger.info(f"Получаю топ {num_pairs} пар (пропускаю первые {skip_top_n})")
        
        pairs = self.bybit.get_trading_pairs(min_volume_usdt=100000)
        
        if not pairs:
            logger.error("Не удалось получить пары для торговли")
            return []
        
        # Пропускаем первые N пар
        trading_pairs = [p['symbol'] for p in pairs[skip_top_n:skip_top_n + num_pairs]]
        
        logger.info(f"Будем торговать {len(trading_pairs)} парами")
        return trading_pairs
    
    def analyze_symbol(self, symbol: str):
        """
        Проанализировать символ используя все стратегии
        
        Args:
            symbol: Торговая пара
        
        Returns:
            dict с сигналом и уверенностью
        """
        try:
            # Получаем данные
            df = self.bybit.get_klines(symbol, interval="5", limit=self.config['lookback_period'] + 10)
            if df is None or len(df) < self.config['lookback_period']:
                return {
                    'symbol': symbol,
                    'signal': None,
                    'confidence': 0,
                    'reason': 'Недостаточно данных'
                }
            
            ticker = self.bybit.get_ticker(symbol)
            orderbook = self.bybit.get_orderbook(symbol)
            
            if ticker is None:
                return {
                    'symbol': symbol,
                    'signal': None,
                    'confidence': 0,
                    'reason': 'Не удалось получить ticker'
                }
            
            # 1. ML LSTM анализ (60%)
            ml_signal = self.lstm.predict(df, return_confidence=True)
            if ml_signal is None:
                ml_signal = {'direction': None, 'confidence': 0, 'raw_prediction': 0.5}
            
            ml_direction = 'BUY' if ml_signal['direction'] == 1 else 'SELL'
            ml_confidence = ml_signal['confidence'] * self.config['ml_weight']
            
            # 2. Mean Reversion анализ (25%)
            mr_result = self.mean_reversion.analyze(df)
            mr_signal = mr_result['signal']
            mr_confidence = mr_result['confidence'] * self.config['mr_weight']
            
            # 3. Microstructure анализ (15%)
            ms_result = self.microstructure.analyze(orderbook, ticker['last_price'])
            ms_signal = ms_result['signal']
            ms_confidence = ms_result['confidence'] * self.config['ms_weight']
            
            # Объединяем сигналы
            buy_confidence = 0
            sell_confidence = 0
            
            if ml_direction == 'BUY':
                buy_confidence += ml_confidence
            else:
                sell_confidence += ml_confidence
            
            if mr_signal == 'BUY':
                buy_confidence += mr_confidence
            elif mr_signal == 'SELL':
                sell_confidence += mr_confidence
            
            if ms_signal == 'BUY':
                buy_confidence += ms_confidence
            elif ms_signal == 'SELL':
                sell_confidence += ms_confidence
            
            # Определяем финальный сигнал
            if buy_confidence > sell_confidence and buy_confidence > self.config['confidence_threshold']:
                final_signal = 'BUY'
                final_confidence = buy_confidence
            elif sell_confidence > buy_confidence and sell_confidence > self.config['confidence_threshold']:
                final_signal = 'SELL'
                final_confidence = sell_confidence
            else:
                final_signal = None
                final_confidence = max(buy_confidence, sell_confidence)
            
            return {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': min(1.0, final_confidence),
                'buy_confidence': buy_confidence,
                'sell_confidence': sell_confidence,
                'ml_signal': ml_direction,
                'ml_confidence': ml_confidence,
                'mr_signal': mr_signal,
                'mr_confidence': mr_confidence,
                'ms_signal': ms_signal,
                'ms_confidence': ms_confidence,
                'current_price': ticker['last_price'],
                'spread': ms_result.get('spread', 0),
                'ml_raw': ml_signal['raw_prediction']
            }
        
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return {
                'symbol': symbol,
                'signal': None,
                'confidence': 0,
                'reason': str(e)
            }
    
    def should_enter_trade(self, symbol: str, signal: dict) -> bool:
        """
        Проверить, должны ли мы входить в торговлю
        
        Returns:
            True если все фильтры пройдены
        """
        if signal['signal'] is None:
            return False
        
        if signal['confidence'] < self.config['confidence_threshold']:
            return False
        
        # Проверяем количество торговли по этому символу
        if self.trades_today[symbol] >= self.config['max_trades_per_symbol_per_day']:
            logger.debug(f"{symbol}: Достигнут лимит сделок за день")
            return False
        
        # Проверяем время последней торговли
        if symbol in self.last_trade_time:
            time_since_last = time.time() - self.last_trade_time[symbol]
            if time_since_last < self.config['min_time_between_trades_seconds']:
                logger.debug(f"{symbol}: Слишком быстро после последней торговли")
                return False
        
        # Проверяем максимальное количество открытых позиций
        open_positions = sum(1 for p in self.positions.values() if p['status'] == 'open')
        if open_positions >= self.config['max_positions']:
            logger.debug(f"Достигнут лимит открытых позиций: {open_positions}")
            return False
        
        return True
    
    def execute_trade(self, symbol: str, signal: dict) -> bool:
        """
        Выполнить торговлю
        
        Args:
            symbol: Торговая пара
            signal: dict с анализом
        
        Returns:
            True если торговля успешна
        """
        try:
            if signal['signal'] not in ['BUY', 'SELL']:
                return False
            
            # Рассчитываем размер позиции
            qty = self._calculate_position_size(symbol, signal)
            if qty <= 0:
                logger.warning(f"{symbol}: Не удалось рассчитать размер позиции")
                return False
            
            # Создаем ордер (используем Market order для скорости)
            order = self.bybit.create_order(
                symbol=symbol,
                side=signal['signal'],
                qty=qty,
                order_type='Market'
            )
            
            if order is None:
                return False
            
            # Сохраняем информацию о позиции
            position_id = order.get('orderId', f"{symbol}_{time.time()}")
            self.positions[position_id] = {
                'symbol': symbol,
                'side': signal['signal'],
                'qty': qty,
                'entry_price': signal['current_price'],
                'entry_time': datetime.now(),
                'status': 'open',
                'confidence': signal['confidence'],
                'order_id': order.get('orderId')
            }
            
            # Обновляем счетчики
            self.trades_today[symbol] += 1
            self.last_trade_time[symbol] = time.time()
            
            logger.info(
                f"Торговля выполнена: {symbol} {signal['signal']} "
                f"{qty} @ {signal['current_price']} (уверенность: {signal['confidence']:.2%})"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Ошибка выполнения торговли для {symbol}: {e}")
            return False
    
    def _calculate_position_size(self, symbol: str, signal: dict) -> float:
        """
        Рассчитать размер позиции на основе уверенности и баланса
        
        Returns:
            Размер позиции в контрактах
        """
        try:
            # Получаем баланс
            balance = self.bybit.get_balance()
            if not balance or 'USDT' not in balance:
                logger.warning(f"Не удалось получить баланс USDT")
                return 0
            
            available_usdt = balance['USDT']['available_balance']
            
            # Базовый размер позиции
            position_size_usdt = self.config['position_size_usdt']
            
            if available_usdt < position_size_usdt:
                logger.warning(f"Недостаточно баланса: {available_usdt} < {position_size_usdt}")
                return 0
            
            # Увеличиваем размер в зависимости от уверенности
            confidence_multiplier = 0.5 + (signal['confidence'] * 1.5)  # 0.5 до 2.0x
            adjusted_size_usdt = position_size_usdt * confidence_multiplier
            
            # Учитываем leverage
            adjusted_size_usdt *= self.config['leverage']
            
            # Получаем цену для перевода в контракты
            current_price = signal['current_price']
            qty = adjusted_size_usdt / current_price
            
            # Округляем до минимальной точности
            qty = round(qty, 4)
            
            return qty
        
        except Exception as e:
            logger.error(f"Ошибка расчета размера позиции: {e}")
            return 0
    
    def manage_open_positions(self):
        """Управлять открытыми позициями (check P&L, stop loss, take profit)"""
        closed_positions = []
        
        for pos_id, position in list(self.positions.items()):
            if position['status'] != 'open':
                continue
            
            try:
                # Получаем текущую позицию
                current_pos = self.bybit.get_position(position['symbol'])
                
                if current_pos is None or current_pos['size'] == 0:
                    # Позиция закрыта
                    position['status'] = 'closed'
                    position['exit_price'] = current_pos['current_price'] if current_pos else position['entry_price']
                    position['exit_time'] = datetime.now()
                    position['pnl'] = current_pos['pnl'] if current_pos else 0
                    position['pnl_percent'] = current_pos['pnl_percent'] if current_pos else 0
                    closed_positions.append(pos_id)
                    
                    logger.info(
                        f"Позиция закрыта: {position['symbol']} "
                        f"P&L: {position['pnl']:.2f} USDT ({position['pnl_percent']:.2%})"
                    )
                    continue
                
                # Проверяем stop loss (-2%)
                if current_pos['pnl_percent'] < -self.config['max_loss_percent'] / 100:
                    logger.warning(f"Stop Loss сработал: {position['symbol']} ({current_pos['pnl_percent']:.2%})")
                    self.bybit.close_position(position['symbol'])
                    continue
                
                # Проверяем take profit (+1%)
                if current_pos['pnl_percent'] > 0.01:
                    logger.info(f"Take Profit: {position['symbol']} ({current_pos['pnl_percent']:.2%})")
                    self.bybit.close_position(position['symbol'])
                    continue
            
            except Exception as e:
                logger.error(f"Ошибка управления позицией {pos_id}: {e}")
        
        # Удаляем закрытые позиции из словаря
        for pos_id in closed_positions:
            del self.positions[pos_id]
    
    def retrain_model_if_needed(self):
        """Переобучить модель каждые N часов"""
        if self.last_retrain_time is None:
            self.last_retrain_time = datetime.now()
        
        hours_since_retrain = (datetime.now() - self.last_retrain_time).total_seconds() / 3600
        
        if hours_since_retrain >= self.config.get('retrain_interval_hours', 4):
            logger.info("Начинаю переобучение модели...")
            
            try:
                # Получаем исторические данные
                sample_symbols = self.get_top_trading_pairs(num_pairs=5, skip_top_n=5)
                
                combined_df = pd.DataFrame()
                for symbol in sample_symbols:
                    df = self.bybit.get_klines(symbol, interval="5", limit=500)
                    if df is not None and len(df) > 0:
                        combined_df = pd.concat([combined_df, df], ignore_index=True)
                
                if len(combined_df) > self.config['lookback_period']:
                    self.lstm.train(combined_df, epochs=20, batch_size=32)
                    self.lstm.save_model('lstm_model')
                    self.last_retrain_time = datetime.now()
                    logger.info("Модель успешно переобучена")
            
            except Exception as e:
                logger.error(f"Ошибка переобучения модели: {e}")
    
    def run_iteration(self, trading_pairs: list):
        """
        Запустить одну итерацию торговли
        
        Args:
            trading_pairs: list с символами пар для торговли
        """
        logger.info(f"Запускаю итерацию торговли ({len(trading_pairs)} пар)...")
        
        # Управляем открытыми позициями
        self.manage_open_positions()
        
        # Переобучаем модель если нужно
        self.retrain_model_if_needed()
        
        # Анализируем все пары
        signals = []
        for symbol in trading_pairs:
            signal = self.analyze_symbol(symbol)
            if signal['signal'] is not None:
                signals.append(signal)
        
        # Сортируем по уверенности
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"Получено {len(signals)} сигналов из {len(trading_pairs)} пар")
        
        # Входим в топ сигналы (соблюдая лимиты позиций)
        trades_executed = 0
        for signal in signals[:10]:  # Топ 10 сигналов
            if self.should_enter_trade(signal['symbol'], signal):
                if self.execute_trade(signal['symbol'], signal):
                    trades_executed += 1
        
        logger.info(f"Выполнено {trades_executed} торговель")
        
        # Выводим статистику
        open_pos_count = sum(1 for p in self.positions.values() if p['status'] == 'open')
        logger.info(f"Открытых позиций: {open_pos_count}, Сделок сегодня: {sum(self.trades_today.values())}")
