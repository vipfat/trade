import pandas as pd
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MicrostructureAnalyzer:
    """
    Анализатор микроструктуры рынка (Order Book анализ)
    Анализирует потоки ордеров и уровни поддержки/сопротивления
    """
    
    def __init__(self, spread_threshold=0.05, order_imbalance_threshold=0.6):
        """
        Args:
            spread_threshold: Максимальный спред в % для торговли
            order_imbalance_threshold: Порог дисбаланса ордеров (0-1)
        """
        self.spread_threshold = spread_threshold
        self.order_imbalance_threshold = order_imbalance_threshold
    
    def analyze(self, orderbook: dict, current_price: float):
        """
        Анализировать order book и определить силу движения
        
        Args:
            orderbook: dict с 'bids' и 'asks' (список [цена, объем])
            current_price: Текущая цена
        
        Returns:
            dict с анализом
        """
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return {
                'signal': None,
                'confidence': 0,
                'reason': 'Нет данных order book'
            }
        
        bids = orderbook['bids']
        asks = orderbook['asks']
        
        if not bids or not asks:
            return {
                'signal': None,
                'confidence': 0,
                'reason': 'Пустой order book'
            }
        
        # Извлекаем цены и объемы
        bid_prices = np.array([b[0] for b in bids])
        bid_volumes = np.array([b[1] for b in bids])
        ask_prices = np.array([a[0] for a in asks])
        ask_volumes = np.array([a[1] for a in asks])
        
        # Вычисляем спред
        best_bid = bid_prices[0]
        best_ask = ask_prices[0]
        spread = (best_ask - best_bid) / current_price * 100
        
        # Если спред слишком большой - не торгуем
        if spread > self.spread_threshold:
            return {
                'signal': None,
                'confidence': 0,
                'reason': f'Спред слишком большой: {spread:.3f}%'
            }
        
        # Анализируем дисбаланс ордеров на лучших уровнях
        bid_power = bid_volumes[:5].sum()  # Объем покупок на топ 5 уровнях
        ask_power = ask_volumes[:5].sum()  # Объем продаж на топ 5 уровнях
        
        total_power = bid_power + ask_power
        if total_power == 0:
            return {
                'signal': None,
                'confidence': 0,
                'reason': 'Нет объема на лучших уровнях'
            }
        
        # Коэффициент силы покупателей (0-1, где 1=абсолютное доминирование покупателей)
        buyer_strength = bid_power / total_power
        seller_strength = ask_power / total_power
        
        # Определяем дисбаланс
        imbalance = abs(buyer_strength - seller_strength)
        
        signal = None
        confidence = 0
        reason = ""
        
        # Если покупатели доминируют - сигнал BUY
        if buyer_strength > self.order_imbalance_threshold:
            signal = 'BUY'
            confidence = min(0.8, imbalance)
            reason = f"Доминирование покупателей: {buyer_strength*100:.1f}% объема"
        
        # Если продавцы доминируют - сигнал SELL
        elif seller_strength > self.order_imbalance_threshold:
            signal = 'SELL'
            confidence = min(0.8, imbalance)
            reason = f"Доминирование продавцов: {seller_strength*100:.1f}% объема"
        
        # Анализируем поддержку/сопротивление
        price_pos = self._analyze_support_resistance(
            bid_prices, bid_volumes, ask_prices, ask_volumes, current_price
        )
        
        if price_pos == 'near_support' and signal != 'SELL':
            confidence = min(1.0, confidence + 0.15)
            reason += " (поблизости поддержка)"
        
        elif price_pos == 'near_resistance' and signal != 'BUY':
            confidence = min(1.0, confidence + 0.15)
            reason += " (поблизости сопротивление)"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reason': reason,
            'bid_power': float(bid_power),
            'ask_power': float(ask_power),
            'buyer_strength': float(buyer_strength),
            'seller_strength': float(seller_strength),
            'imbalance': float(imbalance),
            'spread': float(spread),
            'best_bid': float(best_bid),
            'best_ask': float(best_ask)
        }
    
    @staticmethod
    def _analyze_support_resistance(bid_prices, bid_volumes, ask_prices, ask_volumes, current_price):
        """
        Проанализировать уровни поддержки и сопротивления
        
        Returns:
            'near_support', 'near_resistance', или None
        """
        # Ищем скопления объемов (потенциальные уровни)
        all_bids = list(zip(bid_prices, bid_volumes))
        all_asks = list(zip(ask_prices, ask_volumes))
        
        # Находим уровень максимального объема покупок
        if all_bids:
            max_bid_volume_level = max(all_bids, key=lambda x: x[1])[0]
            # Если это ниже текущей цены - это потенциальная поддержка
            if max_bid_volume_level < current_price:
                support_distance = (current_price - max_bid_volume_level) / current_price * 100
                if support_distance < 0.5:  # Близко
                    return 'near_support'
        
        # Находим уровень максимального объема продаж
        if all_asks:
            max_ask_volume_level = max(all_asks, key=lambda x: x[1])[0]
            # Если это выше текущей цены - это потенциальное сопротивление
            if max_ask_volume_level > current_price:
                resistance_distance = (max_ask_volume_level - current_price) / current_price * 100
                if resistance_distance < 0.5:  # Близко
                    return 'near_resistance'
        
        return None
