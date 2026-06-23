import ccxt
import pandas as pd
import time
import logging
from typing import Optional

# Configuración del Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceClient:
    """
    Cliente para interactuar con la API de Binance vía CCXT.
    Maneja la descarga de datos OHLCV respetando los límites de velocidad (Rate Limits).
    """
    def __init__(self):
        # Inicializamos el exchange activando explícitamente el control de límites
        self.exchange = ccxt.binance({
            'enableRateLimit': True, 
        })
        # Límite máximo de velas por petición que permite Binance
        self.limit_per_request = 1000

    def fetch_historical_data(self, symbol: str, timeframe: str, total_candles: int) -> Optional[pd.DataFrame]:
        """
        Descarga masiva de datos históricos usando paginación. 
        Ideal para entrenar el modelo (Backtesting).
        """
        logger.info(f"Iniciando descarga masiva de {total_candles} velas para {symbol} ({timeframe})...")
        all_bars = []
        
        try:
            timeframe_ms = self.exchange.parse_timeframe(timeframe) * 1000
            since = self.exchange.milliseconds() - (total_candles * timeframe_ms)
            
            while len(all_bars) < total_candles:
                bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=self.limit_per_request)
                
                if not bars:
                    break
                
                since = bars[-1][0] + timeframe_ms
                all_bars.extend(bars)
                
                if len(all_bars) % 5000 == 0:
                    logger.info(f"Progreso: Descargadas {len(all_bars)} / {total_candles} velas...")
                    
        except Exception as e:
            logger.error(f"Error en descarga histórica de Binance: {e}")
            return None

        return self._process_to_dataframe(all_bars, total_candles)

    def fetch_latest_data(self, symbol: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Descarga rápida de las últimas 'n' velas. 
        Ideal para la evaluación en tiempo real (Live Trading).
        """
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            return self._process_to_dataframe(bars, limit)
        except Exception as e:
            logger.error(f"Error en descarga en vivo de Binance: {e}")
            return None

    def _process_to_dataframe(self, bars: list, max_length: int) -> pd.DataFrame:
        """
        Método interno para limpiar y convertir la lista bruta en un DataFrame de Pandas.
        """
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Limpieza crucial: eliminar duplicados por solapamiento de peticiones
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.set_index('timestamp', inplace=True)
        
        # Devolvemos exactamente la cantidad solicitada (recortando el exceso)
        return df.tail(max_length)

# --- Bloque de Prueba Rápida ---
if __name__ == "__main__":
    cliente = BinanceClient()
    print("Probando descarga en vivo (100 velas)...")
    df_live = cliente.fetch_latest_data('BTC/USDT', '5m', 100)
    
    if df_live is not None and not df_live.empty:
        print("✅ Conexión Exitosa. Últimas 5 velas:")
        print(df_live.tail())
        