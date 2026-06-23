import pandas as pd
import numpy as np
import ta
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        pass

    def generate_synthetic_contracts(self, df):
        """
        Calcula indicadores técnicos y construye la variable objetivo (Target)
        evitando el Data Leakage (Fuga de Datos).
        """
        try:
            df = df.copy()

            # 1. FEATURES TÉCNICOS (El "Presente" y el "Pasado")
            # Usamos la librería 'ta' para calcular Momentum, Volatilidad y Tendencia
            df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
            df['atr'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range()
            df['ema_9'] = ta.trend.EMAIndicator(close=df['close'], window=9).ema_indicator()
            df['ema_21'] = ta.trend.EMAIndicator(close=df['close'], window=21).ema_indicator()
            
            # Relaciones matemáticas
            df['tendencia'] = (df['ema_9'] > df['ema_21']).astype(int)
            df['retorno'] = df['close'].pct_change()
            
            # Variable de tiempo para Polymarket (Distancia al vencimiento)
            # Para evitar bugs en live_bot.py, calculamos los minutos hasta el fin del día (UTC)
            if 'timestamp' in df.columns:
                dt = pd.to_datetime(df['timestamp'])
                end_of_day = dt.dt.ceil('D')
                df['time_to_expiry'] = (end_of_day - dt).dt.total_seconds() / 60.0
            else:
                df['time_to_expiry'] = 1440 # Valor por defecto (24 horas)

            # ---------------------------------------------------------
            # 🚨 LA CURA AL DATA LEAKAGE (EL TARGET CORRECTO) 🚨
            # ---------------------------------------------------------
            # Usamos shift(-1) para que el Target de la fila actual sea la dirección de la SIGUIENTE vela.
            # 1 = Subirá | 0 = Bajará
            df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

            # 3. LIMPIEZA DE DATOS
            # Eliminamos las primeras filas que tienen NaN debido al cálculo de las EMAs (21 periodos)
            df.dropna(subset=['ema_21', 'rsi', 'atr'], inplace=True)
            
            # Nota: La última fila del DataFrame tendrá target=0 o NaN porque no conocemos el futuro,
            # pero no importa, porque gracias a nuestra corrección en model.py, a la hora de predecir 
            # en vivo, el modelo ignora la columna 'target' completamente.

            return df

        except Exception as e:
            logger.error(f"Error construyendo features: {e}")
            return pd.DataFrame()
            