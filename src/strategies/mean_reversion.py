import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MeanReversionAnalyzer:
    """
    Анализатор Mean Reversion (возврат к среднему)
    Предполагает, что цена вернется к скользящей средней после отклонения
    """
    
    def __init__(self, sma_period=20, bb_std=2, rsi_period=14):
        """
        Args:
            sma_period: Период простой скользящей средней
            bb_std: Количество стандартных отклонений для Bollinger Bands
            rsi_period: Период для RSI
        """
        self.sma_period = sma_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
    
    def analyze(self, df: pd.DataFrame):
        """
        Анализировать цену на основе mean reversion
        
        Args:
            df: DataFrame с OHLCV данными
        
        Returns:
            dict с сигналами
        """
        if len(df) < max(self.sma_period, self.rsi_period):
            return {
                'signal': None,
                'confidence': 0,
                'reason': 'Недостаточно данных'
            }
        
        close = df['close'].values
        last_price = close[-1]
        
        # Вычисляем SMA
        sma = pd.Series(close).rolling(window=self.sma_period).mean().values
        sma_current = sma[-1]
        
        # Вычисляем Bollinger Bands
        std = pd.Series(close).rolling(window=self.sma_period).std().values
        upper_band = sma + (std * self.bb_std)
        lower_band = sma - (std * self.bb_std)
        
        upper_current = upper_band[-1]
        lower_current = lower_band[-1]
        
        # Вычисляем RSI
        rsi = self._calculate_rsi(close, self.rsi_period)
        rsi_current = rsi[-1]
        
        # Вычисляем отклонение от среднего (%)
        deviation = ((last_price - sma_current) / sma_current) * 100
        
        signal = None
        confidence = 0
        reason = ""
        
        # Логика сигналов
        
        # Если цена выше верхней полосы -> BUY (ожидаем падение)
        if last_price > upper_current:
            signal = 'SELL'  # Ожидаем возврат вниз
            confidence = min(0.8, abs(deviation) / 5)  # Чем больше отклонение, тем выше уверенность
            reason = f"Цена выше верхней полосы на {abs(deviation):.2f}%"
            
            # Если RSI перекуплен - сигнал сильнее
            if rsi_current > 70:
                confidence = min(1.0, confidence + 0.2)
                reason += ", RSI > 70 (перекупленность)"
        
        # Если цена ниже нижней полосы -> SELL (ожидаем рост)
        elif last_price < lower_current:
            signal = 'BUY'  # Ожидаем возврат вверх
            confidence = min(0.8, abs(deviation) / 5)
            reason = f"Цена ниже нижней полосы на {abs(deviation):.2f}%"
            
            # Если RSI перепродан - сигнал сильнее
            if rsi_current < 30:
                confidence = min(1.0, confidence + 0.2)
                reason += ", RSI < 30 (перепроданность)"
        
        # Если близко к средней - сигнал слабый или его нет
        else:
            if abs(deviation) > 2 and rsi_current > 70:
                signal = 'SELL'
                confidence = 0.3
                reason = "Близко к верхней полосе, RSI высокий"
            elif abs(deviation) > 2 and rsi_current < 30:
                signal = 'BUY'
                confidence = 0.3
                reason = "Близко к нижней полосе, RSI низкий"
            else:
                signal = None
                confidence = 0
                reason = "Цена около скользящей средней"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'current_price': last_price,
            'sma': sma_current,
            'upper_band': upper_current,
            'lower_band': lower_current,
            'rsi': rsi_current,
            'deviation_percent': deviation
        }
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Вычислить RSI"""
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
