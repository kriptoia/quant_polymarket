import os
import sys
import time
import logging
import warnings
from datetime import datetime

# Ajustar el path para permitir ejecuciones desde la raíz con `python src/live_bot.py`
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Importamos el notificador de Telegram
from src.notifications.telegram_bot import send_telegram_alert

# Suprimir warnings en consola (evita mensajes como NotOpenSSLWarning)
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

# Configuración de Logging para producción (Escribe en consola)
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

    # Inyectamos el Token ID real DIARIO de Bitcoin (> $64,000)
    TOKEN_ID_OBJETIVO = "84222163613913931833893267542914376578407462311561823691273599611948719713378"

    bankroll_actual = BANKROLL_INICIAL

    # Desactivamos temporalmente la lista de rotación automática para forzar el uso de este Token
    tokens_list = [TOKEN_ID_OBJETIVO]
    ROTATION_INTERVAL = 0  

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

    # ACTIVAMOS los logs detallados para ver la matemática del Guardián (NUEVO)
    logging.getLogger('src.execution.edge_calc').setLevel(logging.INFO)
    logging.getLogger('src.execution.position_sizing').setLevel(logging.INFO)

    # 3. Bucle Principal de Producción
    ciclo = 1
    while True:
        try:
            logger.info(f"--- Escaneo #{ciclo} | Capital Simulado: ${bankroll_actual:.2f} ---")
            
            # A. Leer el mercado actual de Binance (Últimas 400 velas para evitar bugs de apertura)
            df_live_raw = binance.fetch_latest_data(SYMBOL_BINANCE, TIMEFRAME, 400)
            if df_live_raw is None:
                raise ValueError("Fallo al conectar con Binance.")

            # B. Procesar Features
            df_live_processed = engineer.generate_synthetic_contracts(df_live_raw)
            if df_live_processed.empty:
                logger.warning("No se generaron features válidos para los datos actuales. Reintentando en 60 segundos.")
                time.sleep(60)
                continue

            vela_actual = df_live_processed.iloc[-1]

            # Filtro de tiempo: Si el oráculo de Polymarket cierra en menos de 2 horas, es muy ruidoso
            if vela_actual['time_to_expiry'] < 120:
                logger.warning("Contrato muy cerca de expirar (< 2h). Esperando nuevo ciclo diario.")
                time.sleep(300) # Dormimos 5 minutos y reevaluamos
                continue

            # C. ¿Qué dice nuestra Inteligencia Artificial?
            prob_yes = oraculo.predict_probability(df_live_processed)
            
            # D. ¿Qué dice la multitud humana en Polymarket?
            current_token = TOKEN_ID_OBJETIVO
            logger.info(f"Consultando token: {current_token}")
            
            orderbook = polymarket.get_orderbook(current_token)
            
            # Si se queda sin liquidez, intenta buscar uno nuevo
            if not orderbook:
                logger.warning("Mercado de Polymarket sin liquidez o API caída. Intentando descubrir token activo alternativo...")
                nuevo_token = polymarket.find_active_btc_token()
                if nuevo_token and nuevo_token != current_token:
                    logger.info(f"Token alternativo encontrado: {nuevo_token}. Actualizando objetivo.")
                    TOKEN_ID_OBJETIVO = nuevo_token
                    current_token = nuevo_token
                    orderbook = polymarket.get_orderbook(current_token)

            if not orderbook:
                logger.warning("Mercado de Polymarket sin liquidez o API caída. Saltando ciclo.")
                time.sleep(60)
                continue

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
                    # G. DISPARO VIRTUAL (PAPER TRADE) Y ALERTA TELEGRAM
                    print("\n" + "="*50)
                    print("🚨 ¡ANOMALÍA DETECTADA! DISPARANDO ORDEN 🚨")
                    print("="*50 + "\n")
                    
                    # Construir el mensaje formateado para Telegram
                    mensaje_tg = (
                        f"🚨 <b>¡GANGA MATEMÁTICA DETECTADA!</b> 🚨\n\n"
                        f"📈 <b>Lado a operar:</b> Comprar {oportunidad['side']}\n"
                        f"🧠 <b>Probabilidad IA:</b> {prob_yes*100:.2f}%\n"
                        f"🧑‍🤝‍🧑 <b>Prob. Mercado:</b> {oportunidad['prob_mercado']*100:.2f}%\n"
                        f"🔥 <b>Edge Neto (Ventaja Libre):</b> {oportunidad['edge']*100:.2f}%\n"
                        f"💰 <b>Inversión (Kelly):</b> ${tamaño_inversion:.2f} USDC\n\n"
                        f"🔗 <a href='https://polymarket.com/'>Abrir Polymarket</a>"
                    )
                    
                    # Enviar la alerta al celular
                    send_telegram_alert(mensaje_tg)
                    
                    # Para evitar que el bot se vuelva loco y compre 10 veces en el mismo minuto, 
                    # lo hacemos dormir unos minutos.
                    logger.info("Orden simulada y alerta de Telegram enviada. Durmiendo el bot por 5 minutos para evitar sobreexposición...")
                    time.sleep(300)
            else:
                logger.info(f"Mercado eficiente. Probabilidad IA: {prob_yes:.2f} | Midprice Polymarket: {orderbook['midprice']:.2f}")

            # H. Dormir el bot para no exceder los límites de la API de Binance/Polymarket
            ciclo += 1
            time.sleep(60) # Escaneamos el mercado cada 60 segundos

        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}")
            logger.info("Reintentando en 60 segundos para evitar colapso del sistema...")
            time.sleep(60)

if __name__ == "__main__":
    # Ejecutar el Orquestador
    run_live_bot()