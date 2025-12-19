import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import os
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LSTMPricePredictor:
    """
    LSTM модель для предсказания направления цены
    Предсказывает будет ли цена расти или падать в течение следующих 5-15 минут
    """
    
    def __init__(self, lookback_period=100, model_dir='models_saved'):
        """
        Args:
            lookback_period: Количество свечей для входных данных (100 свечей = 500 минут = 8.3 часа)
            model_dir: Директория для сохранения моделей
        """
        self.lookback_period = lookback_period
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.is_trained = False
        
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Подготовить признаки для модели
        
        Используем:
        - Close, High, Low (нормализованные)
        - Volume (нормализованный)
        - RSI (Relative Strength Index)
        - MACD
        """
        
        features = pd.DataFrame()
        
        # Цена
        features['close'] = df['close']
        features['high'] = df['high']
        features['low'] = df['low']
        features['volume'] = df['volume']
        
        # RSI (Relative Strength Index)
        features['rsi'] = self._calculate_rsi(df['close'], period=14)
        
        # MACD
        macd_data = self._calculate_macd(df['close'])
        features['macd'] = macd_data['macd']
        features['signal'] = macd_data['signal']
        
        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(df['close'])
        features['bb_position'] = bb_data['position']  # 0-1: где цена в пределах полос
        
        # Заполняем NaN значения
        features = features.fillna(method='bfill').fillna(method='ffill')
        
        return features.values
    
    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Вычислить RSI (Relative Strength Index)"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
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
    
    @staticmethod
    def _calculate_macd(prices, fast=12, slow=26, signal=9):
        """Вычислить MACD"""
        ema_fast = pd.Series(prices).ewm(span=fast).mean().values
        ema_slow = pd.Series(prices).ewm(span=slow).mean().values
        macd = ema_fast - ema_slow
        signal_line = pd.Series(macd).ewm(span=signal).mean().values
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': macd - signal_line
        }
    
    @staticmethod
    def _calculate_bollinger_bands(prices, period=20, num_std=2):
        """Вычислить Bollinger Bands"""
        sma = pd.Series(prices).rolling(window=period).mean().values
        std = pd.Series(prices).rolling(window=period).std().values
        
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        
        # Позиция цены между полосами (0-1)
        position = np.where(
            upper != lower,
            (prices - lower) / (upper - lower),
            0.5
        )
        position = np.clip(position, 0, 1)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'position': position
        }
    
    def _create_sequences(self, features: np.ndarray, labels: np.ndarray):
        """Создать последовательности для LSTM"""
        X, y = [], []
        
        for i in range(len(features) - self.lookback_period):
            X.append(features[i:i + self.lookback_period])
            y.append(labels[i + self.lookback_period])
        
        return np.array(X), np.array(y)
    
    def _build_model(self, input_shape):
        """Построить LSTM модель"""
        model = keras.Sequential([
            LSTM(128, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(64, activation='relu', return_sequences=True),
            Dropout(0.2),
            LSTM(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')  # sigmoid для классификации 0-1 (down-up)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, df: pd.DataFrame, epochs=50, batch_size=32, validation_split=0.2):
        """
        Обучить модель
        
        Args:
            df: DataFrame с OHLCV данными (columns: open, high, low, close, volume)
            epochs: Количество эпох обучения
            batch_size: Размер батча
            validation_split: Доля данных для валидации
        """
        logger.info(f"Начинаю обучение модели на {len(df)} свечах")
        
        # Подготавливаем признаки
        features = self._prepare_features(df)
        
        # Нормализуем признаки
        features_scaled = self.scaler.fit_transform(features)
        
        # Создаем целевую переменную (1 если цена вверх, 0 если вниз)
        target = np.where(df['close'].shift(-1) > df['close'], 1, 0)
        target = target[:-1]  # Выравниваем размер
        
        # Создаем последовательности
        X, y = self._create_sequences(features_scaled, target)
        
        logger.info(f"Размер данных для обучения: X={X.shape}, y={y.shape}")
        
        if len(X) < 100:
            logger.warning(f"Слишком мало данных для обучения: {len(X)}")
            return False
        
        # Строим модель
        self.model = self._build_model((X.shape[1], X.shape[2]))
        
        # Обучаем
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        self.is_trained = True
        logger.info("Модель успешно обучена")
        
        return True
    
    def predict(self, df: pd.DataFrame, return_confidence=True):
        """
        Предсказать направление цены
        
        Args:
            df: DataFrame с OHLCV данными
            return_confidence: Возвращать ли уровень уверенности (0-1)
        
        Returns:
            1 если ожидается рост, 0 если падение (и confidence если requested)
        """
        if not self.is_trained or self.model is None:
            logger.warning("Модель еще не обучена")
            return None
        
        if len(df) < self.lookback_period:
            logger.warning(f"Недостаточно данных: {len(df)} < {self.lookback_period}")
            return None
        
        # Подготавливаем последние данные
        features = self._prepare_features(df.tail(self.lookback_period + 1))
        features_scaled = self.scaler.transform(features)
        
        X = features_scaled[-self.lookback_period:].reshape(1, self.lookback_period, features.shape[1])
        
        # Предсказываем
        prediction = self.model.predict(X, verbose=0)[0][0]
        
        if return_confidence:
            return {
                'direction': 1 if prediction > 0.5 else 0,  # 1=up, 0=down
                'confidence': max(prediction, 1 - prediction),
                'raw_prediction': float(prediction)
            }
        else:
            return 1 if prediction > 0.5 else 0
    
    def save_model(self, name: str = 'lstm_model'):
        """Сохранить модель"""
        if self.model is None:
            logger.warning("Нечего сохранять: модель не создана")
            return False
        
        path = os.path.join(self.model_dir, f'{name}.keras')
        self.model.save(path)
        
        # Сохраняем и скейлер
        import pickle
        scaler_path = os.path.join(self.model_dir, f'{name}_scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"Модель сохранена в {path}")
        return True
    
    def load_model(self, name: str = 'lstm_model'):
        """Загрузить модель"""
        path = os.path.join(self.model_dir, f'{name}.keras')
        
        if not os.path.exists(path):
            logger.error(f"Файл модели не найден: {path}")
            return False
        
        self.model = keras.models.load_model(path)
        
        # Загружаем скейлер
        import pickle
        scaler_path = os.path.join(self.model_dir, f'{name}_scaler.pkl')
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
        
        self.is_trained = True
        logger.info(f"Модель загружена из {path}")
        return True
