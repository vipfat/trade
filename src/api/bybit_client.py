import os
from pybit.unified_trading import HTTP, WebSocket
from dotenv import load_dotenv
import pandas as pd
import time
from src.utils.logger import setup_logger

load_dotenv()

logger = setup_logger(__name__)

class BybitClient:
    """Клиент для работы с Bybit API"""
    
    def __init__(self):
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.testnet = os.getenv('BYBIT_TESTNET', 'False').lower() == 'true'
        
        # Инициализируем клиент
        self.client = HTTP(
            testnet=self.testnet,
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        
        logger.info(f"Bybit клиент инициализирован (testnet={self.testnet})")
    
    def get_klines(self, symbol: str, interval: str = "5", limit: int = 100):
        """
        Получить свечи (OHLCV данные)
        
        Args:
            symbol: Торговая пара (например, 'BTCUSDT')
            interval: Таймфрейм ('1', '5', '15', '60', '240', '1D')
            limit: Количество свечей
        
        Returns:
            DataFrame с OHLCV данными
        """
        try:
            response = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            klines = response['result']['list']
            # Свечи приходят в обратном порядке, разворачиваем
            klines.reverse()
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Конвертируем в нужные типы
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                df[col] = pd.to_numeric(df[col])
            
            return df
        
        except Exception as e:
            logger.error(f"Ошибка получения свечей для {symbol}: {e}")
            return None
    
    def get_orderbook(self, symbol: str, limit: int = 25):
        """
        Получить order book (стакан ордеров)
        
        Args:
            symbol: Торговая пара
            limit: Глубина стакана
        
        Returns:
            dict с bids и asks
        """
        try:
            response = self.client.get_orderbook(
                category="linear",
                symbol=symbol,
                limit=limit
            )
            
            orderbook = {
                'bids': [[float(p), float(s)] for p, s in response['result']['b']],
                'asks': [[float(p), float(s)] for p, s in response['result']['a']],
                'timestamp': int(response['result']['ts'])
            }
            
            return orderbook
        
        except Exception as e:
            logger.error(f"Ошибка получения order book для {symbol}: {e}")
            return None
    
    def get_ticker(self, symbol: str):
        """Получить последнюю информацию по паре"""
        try:
            response = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            ticker = response['result']['list'][0]
            return {
                'symbol': ticker['symbol'],
                'last_price': float(ticker['lastPrice']),
                'bid': float(ticker['bid1Price']),
                'ask': float(ticker['ask1Price']),
                'volume_24h': float(ticker['volume24h']),
                'turnover_24h': float(ticker['turnover24h'])
            }
        
        except Exception as e:
            logger.error(f"Ошибка получения ticker для {symbol}: {e}")
            return None
    
    def get_trading_pairs(self, min_volume_usdt: float = 100000):
        """
        Получить список торговых пар с минимальным объемом
        
        Args:
            min_volume_usdt: Минимальный 24h объем в USDT
        
        Returns:
            list с символами пар, отсортированными по объему (убывание)
        """
        try:
            response = self.client.get_tickers(category="linear")
            
            pairs = []
            for ticker in response['result']['list']:
                volume_24h = float(ticker['turnover24h'])
                
                if volume_24h >= min_volume_usdt and 'USDT' in ticker['symbol']:
                    pairs.append({
                        'symbol': ticker['symbol'],
                        'volume': volume_24h
                    })
            
            # Сортируем по объему (убывание)
            pairs.sort(key=lambda x: x['volume'], reverse=True)
            
            return pairs
        
        except Exception as e:
            logger.error(f"Ошибка получения списка пар: {e}")
            return []
    
    def create_order(self, symbol: str, side: str, qty: float, price: float = None, order_type: str = "Limit"):
        """
        Создать ордер
        
        Args:
            symbol: Торговая пара
            side: 'Buy' или 'Sell'
            qty: Количество контрактов
            price: Цена (для лимит-ордеров)
            order_type: 'Limit' или 'Market'
        
        Returns:
            dict с информацией о заказе
        """
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': qty,
                'timeInForce': 'IOC' if order_type == 'Market' else 'GTC'
            }
            
            if order_type == 'Limit' and price:
                params['price'] = price
            
            response = self.client.place_order(**params)
            
            logger.info(f"Ордер создан: {symbol} {side} {qty} по цене {price}")
            return response['result']
        
        except Exception as e:
            logger.error(f"Ошибка создания ордера: {e}")
            return None
    
    def close_position(self, symbol: str):
        """Закрыть позицию по рыночной цене"""
        try:
            # Сначала получаем позицию
            position = self.get_position(symbol)
            if not position or position['size'] == 0:
                logger.warning(f"Нет открытой позиции по {symbol}")
                return None
            
            # Определяем сторону для закрытия (противоположная текущей)
            close_side = 'Sell' if position['side'] == 'Buy' else 'Buy'
            
            response = self.client.place_order(
                category='linear',
                symbol=symbol,
                side=close_side,
                orderType='Market',
                qty=position['size'],
                timeInForce='IOC'
            )
            
            logger.info(f"Позиция закрыта: {symbol}")
            return response['result']
        
        except Exception as e:
            logger.error(f"Ошибка закрытия позиции: {e}")
            return None
    
    def get_position(self, symbol: str = None):
        """Получить информацию о позициях"""
        try:
            response = self.client.get_positions(
                category='linear',
                symbol=symbol
            )
            
            if response['result']['list']:
                pos = response['result']['list'][0]
                return {
                    'symbol': pos['symbol'],
                    'side': pos['side'],
                    'size': float(pos['size']),
                    'entry_price': float(pos['avgPrice']),
                    'current_price': float(pos['markPrice']),
                    'pnl': float(pos['unrealisedPnl']),
                    'pnl_percent': float(pos['unrealisedPnlPct'])
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка получения позиции: {e}")
            return None
    
    def get_balance(self):
        """Получить баланс кошелька"""
        try:
            response = self.client.get_wallet_balance(accountType="UNIFIED")
            
            balance_info = {}
            for coin in response['result']['list'][0]['coin']:
                balance_info[coin['coin']] = {
                    'wallet_balance': float(coin['walletBalance']),
                    'available_balance': float(coin['availableToWithdraw'])
                }
            
            return balance_info
        
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return None
