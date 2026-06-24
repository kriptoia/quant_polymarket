import os
import sys

# Auto-execute inside the virtual environment if it exists and we aren't already in it
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
venv_python_win = os.path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe')
venv_python_unix = os.path.join(ROOT_DIR, '.venv', 'bin', 'python')
venv_python = venv_python_win if os.path.exists(venv_python_win) else venv_python_unix

if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    import subprocess
    sys.exit(subprocess.call([venv_python] + sys.argv))

# Configure UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import time
import logging
import warnings
from datetime import datetime

# Ajustar el path para permitir ejecuciones desde la raíz
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Importamos el notificador de Telegram
from src.notifications.telegram_bot import send_telegram_alert

# Suprimir warnings en consola
warnings.filterwarnings("ignore")

# Reducir ruido de logs de terceros
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('src.api_clients.binance_client').setLevel(logging.WARNING)

# Importamos nuestros módulos Quant
from src.config import SYMBOL_BINANCE, TIMEFRAME, BANKROLL_INICIAL
from src.api_clients.binance_client import BinanceClient
from src.api_clients.poly_client import PolymarketClient
from src.core.features import FeatureEngineer
from src.core.model import PolymarketModel
from src.execution.edge_calc import EdgeCalculator
from src.execution.position_sizing import PositionSizer

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_live_bot():
    print("==================================================")
    print(" 🚀 INICIANDO QUANT BOT EN VIVO (PAPER TRADING) 🚀")
    print("==================================================")

    # 1. Instanciar todos los módulos
    binance = BinanceClient()
    polymarket = PolymarketClient()
    engineer = FeatureEngineer()
    oraculo = PolymarketModel()
    edge_calc = EdgeCalculator()
    sizer = PositionSizer()

    # Token de inicio (Puede ser cualquiera, el bot lo cambiará si no hay liquidez)
    TOKEN_ID_OBJETIVO = "91228418858515776333909499302819175361983659611801615451798481215577008271021"

    bankroll_actual = BANKROLL_INICIAL

    # 2. Fase de Calentamiento (Entrenamiento del Cerebro)
    logger.info("Fase 1: Calentando motores y descargando contexto histórico...")
    df_raw_hist = binance.fetch_historical_data(SYMBOL_BINANCE, TIMEFRAME, 5000)
    
    if df_raw_hist is None or df_raw_hist.empty:
        logger.error("No se pudo descargar datos históricos. Abortando misión.")
        return

    logger.info("Fase 2: Construyendo contratos sintéticos y entrenando IA...")
    df_processed_hist = engineer.generate_synthetic_contracts(df_raw_hist)
    oraculo.train(df_processed_hist)
    logger.info("✅ Cerebro calibrado y listo para operar.")

    print("\n==================================================")
    print(" 📡 ENTRANDO A BUCLE DE ESCANEO INFINITO (24/7) 📡")
    print("==================================================\n")

    # ACTIVAMOS los logs detallados para ver la matemática del Guardián
    logging.getLogger('src.execution.edge_calc').setLevel(logging.INFO)
    logging.getLogger('src.execution.position_sizing').setLevel(logging.INFO)

    # 3. Bucle Principal de Producción
    ciclo = 1
    while True:
        try:
            logger.info(f"--- Escaneo #{ciclo} | Capital Simulado: ${bankroll_actual:.2f} ---")
            
            # A. Leer el mercado actual de Binance
            df_live_raw = binance.fetch_latest_data(SYMBOL_BINANCE, TIMEFRAME, 400)
            if df_live_raw is None:
                raise ValueError("Fallo al conectar con Binance.")

            # B. Procesar Features
            df_live_processed = engineer.generate_synthetic_contracts(df_live_raw)
            if df_live_processed.empty:
                logger.warning("No se generaron features válidos. Reintentando en 60 segundos.")
                time.sleep(60)
                continue

            vela_actual = df_live_processed.iloc[-1]

            # Filtro de tiempo: Si el oráculo de Polymarket cierra en menos de 2 horas, es muy ruidoso
            if vela_actual['time_to_expiry'] < 120:
                logger.warning("Contrato muy cerca de expirar (< 2h). Esperando nuevo ciclo diario.")
                time.sleep(300)
                continue

            # C. ¿Qué dice nuestra Inteligencia Artificial?
            prob_yes = oraculo.predict_probability(df_live_processed)
            
            # D. ¿Qué dice la multitud humana en Polymarket?
            logger.info(f"Consultando token actual: {TOKEN_ID_OBJETIVO}")
            orderbook = polymarket.get_orderbook(TOKEN_ID_OBJETIVO)
            
            # --- SISTEMA DE ROTACIÓN AUTOMÁTICA ---
            necesita_rotacion = False
            
            if not orderbook:
                necesita_rotacion = True
            else:
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])
                if not bids or not asks:
                    necesita_rotacion = True
                else:
                    best_bid = float(bids[-1]['price'])
                    best_ask = float(asks[-1]['price'])
                    spread = best_ask - best_bid
                    
                    # Ignorar sistemáticamente patrón bid 0 / ask 1 o spread inoperable
                    if best_bid == 0 or best_ask >= 0.99 or spread > 0.15:
                        logger.warning(f"⚠️ Fiesta Vacía detectada (Bid: {best_bid}, Ask: {best_ask}, Spread: {spread:.2f}).")
                        necesita_rotacion = True

            if necesita_rotacion:
                logger.info("🔄 Iniciando rotación automática hacia un token BTC vivo...")
                nuevo_token = polymarket.find_liquid_btc_token()
                
                if nuevo_token:
                    logger.info("🎯 Target Actualizado con éxito.")
                    TOKEN_ID_OBJETIVO = nuevo_token
                    orderbook = polymarket.get_orderbook(TOKEN_ID_OBJETIVO)
                else:
                    logger.warning("Zzz... No hay mercados vivos. El bot dormirá hasta que regrese la liquidez.")
                    ciclo += 1
                    time.sleep(60)
                    continue
            # ----------------------------------------

            # E. El Guardián: ¿Hay una ganga matemática real?
            oportunidad = edge_calc.evaluate_opportunity(prob_yes, orderbook)

            if oportunidad:
                # F. Position Sizing: ¿Cuánto dinero arriesgamos?
                tamaño_inversion = sizer.calculate_size(
                    edge_neto=oportunidad['edge'],
                    prob_mercado=oportunidad['prob_mercado'],
                    liquidez_disponible=oportunidad['liquidez_disponible'],
                    bankroll=bankroll_actual
                )

                if tamaño_inversion > 0:
                    # G. DISPARO VIRTUAL E INYECCIÓN DE TÍTULO PARA TELEGRAM
                    print("\n" + "="*50)
                    print("🚨 ¡ANOMALÍA DETECTADA! DISPARANDO ORDEN 🚨")
                    print("="*50 + "\n")
                    
                    # Llamamos a la función auxiliar para obtener el título en este preciso momento
                    titulo_mercado = polymarket.get_market_title_by_token(TOKEN_ID_OBJETIVO)
                    
                    # Construir el mensaje formateado para Telegram
                    mensaje_tg = (
                        f"🚨 <b>¡GANGA MATEMÁTICA DETECTADA!</b> 🚨\n\n"
                        f"🎯 <b>Mercado:</b> {titulo_mercado}\n"
                        f"🔑 <b>Token ID:</b> <code>{TOKEN_ID_OBJETIVO}</code>\n"
                        f"📈 <b>Lado a operar:</b> Comprar {oportunidad['side']}\n"
                        f"🧠 <b>Probabilidad IA:</b> {prob_yes*100:.2f}%\n"
                        f"🧑‍🤝‍🧑 <b>Prob. Mercado:</b> {oportunidad['prob_mercado']*100:.2f}%\n"
                        f"🔥 <b>Edge Neto:</b> {oportunidad['edge']*100:.2f}%\n"
                        f"💰 <b>Inversión:</b> ${tamaño_inversion:.2f} USDC\n\n"
                        f"🔗 <a href='https://polymarket.com/'>Abrir Polymarket</a>"
                    )
                    
                    send_telegram_alert(mensaje_tg)
                    
                    logger.info("Orden simulada y alerta de Telegram enviada. Durmiendo 5 minutos...")
                    time.sleep(300)
            else:
                logger.info(f"Mercado eficiente. Probabilidad IA: {prob_yes:.2f} | Midprice Polymarket: {orderbook.get('midprice', 0.50):.2f}")

            # H. Dormir el bot para no exceder los límites de la API
            ciclo += 1
            time.sleep(60)

        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}")
            logger.info("Reintentando en 60 segundos...")
            time.sleep(60)

if __name__ == "__main__":
    run_live_bot()