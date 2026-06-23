import os
from dotenv import load_dotenv
from pathlib import Path

# Carga las variables ocultas del archivo .env
load_dotenv()

# ==========================================
# 1. RUTAS DEL SISTEMA (PORTABILIDAD)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. SEGURIDAD Y CREDENCIALES API
# ==========================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

POLY_API_KEY = os.getenv("POLY_API_KEY")
POLY_SECRET = os.getenv("POLY_SECRET")
POLY_PASSPHRASE = os.getenv("POLY_PASSPHRASE")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Telegram Alertas
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================
# 3. PARÁMETROS DEL MOTOR QUANT Y RIESGO
# ==========================================
SYMBOL_BINANCE = 'BTC/USDT'
TIMEFRAME = '5m'

# Fricción y Exigencia del Mercado (NUEVOS FILTROS QUANT)
FEE_EFECTIVA = 0.02       # 2% sobre ganancias netas
COLCHON_MODELO = 0.05     # 5% de margen por error de calibración
MIN_EDGE_REQUIRED = 0.10  # NUEVO: Exigir al menos 10% de Edge Neto puro
MAX_PRICE_PAY = 0.60      # NUEVO: Prohibido comprar acciones por encima de $0.60 (Busca Underdogs)

# Gestión de Capital (Kelly Fraccional Conservador)
BANKROLL_INICIAL = 50.0 
KELLY_CAP = 0.02          # Límite absoluto del 2% del bankroll por trade
KELLY_FRACTION = 0.10     # 1/10 de Kelly (Para proteger la curva de capital)

# Sincronización del Oráculo
ORACLE_RESOLUTION_HOUR = 12
ORACLE_RESOLUTION_MINUTE = 0
