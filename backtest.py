import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import sys
from tqdm import tqdm

# Configure UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Importamos nuestros módulos Quant
from src.config import BANKROLL_INICIAL, FEE_EFECTIVA
from src.api_clients.binance_client import BinanceClient
from src.core.features import FeatureEngineer
from src.core.model import PolymarketModel
from src.execution.edge_calc import EdgeCalculator
from src.execution.position_sizing import PositionSizer

# Configuración básica de logs para la consola principal
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def run_backtest():
    print("🚀 INICIANDO SIMULADOR QUANT (BACKTEST) 🚀")

    # 1. Instanciar todos los módulos de nuestra arquitectura
    binance = BinanceClient()
    engineer = FeatureEngineer()
    oraculo = PolymarketModel()
    edge_calc = EdgeCalculator()
    sizer = PositionSizer()

    # 2. Descargar Datos Crudos
    print("\n📥 1. Descargando datos históricos de Binance...")
    df_raw = binance.fetch_historical_data('BTC/USDT', '5m', 15000)
    if df_raw is None or df_raw.empty:
        print("❌ Error descargando datos. Revisa tu conexión.")
        return

    # 3. Ingeniería de Datos
    print("⚙️ 2. Construyendo contratos sintéticos y features...")
    df_processed = engineer.generate_synthetic_contracts(df_raw)

    # 4. División de Datos (80% Entrenamiento, 20% Prueba Walk-Forward)
    split_idx = int(len(df_processed) * 0.8)
    df_train = df_processed.iloc[:split_idx]
    df_test = df_processed.iloc[split_idx:]

    # 5. Entrenamiento del Cerebro
    print("\n🧠 3. Entrenando Inteligencia Artificial XGBoost...")
    oraculo.train(df_train)

    # 6. Simulación Financiera
    print("\n💸 4. Iniciando Simulación de Capital (Polymarket Virtual)...")
    bankroll = BANKROLL_INICIAL
    historial_capital = [bankroll]
    
    # --- NUEVAS MÉTRICAS DE AUDITORÍA ---
    trades_ejecutados = 0
    ganancias_array = []
    perdidas_array = []

    # Desactivamos los logs detallados de ejecución para no inundar la consola en el bucle
    logging.getLogger('src.execution.edge_calc').setLevel(logging.WARNING)
    logging.getLogger('src.execution.position_sizing').setLevel(logging.WARNING)

    # Iteramos sobre el set de prueba vela por vela
    for i in tqdm(range(len(df_test)), desc="Simulando Mercado"):
        # Simulamos que estamos en este momento exacto del tiempo
        current_time_slice = df_test.iloc[:i+1]
        row_actual = current_time_slice.iloc[-1]

        # Filtro temporal: No operamos a menos de 2 horas del cierre
        if row_actual['time_to_expiry'] < 120:
            historial_capital.append(bankroll)
            continue

        # a) Predicción de la Inteligencia Artificial
        prob_yes = oraculo.predict_probability(current_time_slice)

        # b) Simulación del Order Book de Polymarket
        ruido_mercado = np.random.uniform(-0.25, 0.25)
        midprice_simulado = np.clip(prob_yes + ruido_mercado, 0.05, 0.95)

        orderbook_simulado = {
            "best_bid": midprice_simulado - 0.01,
            "best_ask": midprice_simulado + 0.01,
            "bid_size": 2000.0,
            "ask_size": 2000.0,
            "midprice": midprice_simulado,
            "spread": 0.02
        }

        # c) Cálculo de Edge
        oportunidad = edge_calc.evaluate_opportunity(prob_yes, orderbook_simulado)

        if oportunidad:
            # d) Position Sizing (Aplicando Kelly Ajustado)
            tamaño_inversion = sizer.calculate_size(
                edge_neto=oportunidad['edge'],
                prob_mercado=oportunidad['prob_mercado'],
                liquidez_disponible=oportunidad['liquidez_disponible'],
                bankroll=bankroll
            )

            if tamaño_inversion > 0:
                trades_ejecutados += 1
                resolucion_real = row_actual['target'] # 1 si subió, 0 si bajó

                # e) Resolución Financiera con CORRECCIÓN DE PAYOFF Y FEES
                if oportunidad['side'] == 'YES':
                    if resolucion_real == 1:
                        # Paga el precio Ask hoy. Si gana, la acción vale $1.
                        acciones_compradas = tamaño_inversion / orderbook_simulado['best_ask']
                        ganancia_bruta = (acciones_compradas * 1.0) - tamaño_inversion
                        ganancia_neta = ganancia_bruta * (1 - FEE_EFECTIVA) # Fee solo sobre profit
                        
                        bankroll += ganancia_neta
                        ganancias_array.append(ganancia_neta)
                    else:
                        bankroll -= tamaño_inversion
                        perdidas_array.append(tamaño_inversion)

                elif oportunidad['side'] == 'NO':
                    if resolucion_real == 0:
                        # Comprar NO significa comprar al (1 - best_bid)
                        precio_no = 1.0 - orderbook_simulado['best_bid']
                        acciones_compradas = tamaño_inversion / precio_no
                        ganancia_bruta = (acciones_compradas * 1.0) - tamaño_inversion
                        ganancia_neta = ganancia_bruta * (1 - FEE_EFECTIVA)
                        
                        bankroll += ganancia_neta
                        ganancias_array.append(ganancia_neta)
                    else:
                        bankroll -= tamaño_inversion
                        perdidas_array.append(tamaño_inversion)

        historial_capital.append(bankroll)

        # Control de Ruina
        if bankroll <= 0:
            print("\n💀 BANCARROTA. El algoritmo ha perdido todo el capital.")
            break

    # 7. Resultados Finales y Auditoría Quant
    print("\n\n=========================================")
    print("🏆 RESULTADOS DEL BACKTEST (VERSIÓN CONSERVADORA) 🏆")
    print("=========================================")
    print(f"Capital Inicial: ${BANKROLL_INICIAL:,.2f} USDC")
    print(f"Capital Final:   ${bankroll:,.2f} USDC")
    
    rendimiento = ((bankroll - BANKROLL_INICIAL) / BANKROLL_INICIAL) * 100
    print(f"Rendimiento Neto: {rendimiento:,.2f}%\n")
    
    print("--- MÉTRICAS DE OPERATIVA ---")
    print(f"Total Trades Ejecutados: {trades_ejecutados}")
    
    if trades_ejecutados > 0:
        trades_ganados = len(ganancias_array)
        win_rate = (trades_ganados / trades_ejecutados) * 100
        print(f"Win Rate (Aciertos): {win_rate:.2f}%")
        
        avg_win = np.mean(ganancias_array) if ganancias_array else 0
        avg_loss = np.mean(perdidas_array) if perdidas_array else 0
        
        print(f"\n--- AUDITORÍA DE RIESGO (ASIMETRÍA) ---")
        print(f"Ganancia Media por Trade (+): ${avg_win:.2f} USDC")
        print(f"Pérdida Media por Trade (-): ${avg_loss:.2f} USDC")
        
        if avg_loss > 0:
            ratio_riesgo_beneficio = avg_win / avg_loss
            print(f"Ratio Riesgo/Beneficio (G:L): {ratio_riesgo_beneficio:.2f} : 1")
            
            # Cálculo de la Esperanza Matemática (Expectancy)
            expectancy = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
            print(f"Esperanza Matemática (Por Trade): ${expectancy:.2f} USDC")

    # 8. Renderizado de la Curva de Capital (Equity Curve)
    plt.style.use('dark_background')
    plt.figure(figsize=(12, 6))
    
    color_linea = 'lime' if bankroll > BANKROLL_INICIAL else 'red'
    plt.plot(historial_capital, color=color_linea, linewidth=2)
    
    plt.title('Curva de Capital (Equity Curve) - Arbitraje Quant Polymarket', fontsize=14, pad=15)
    plt.xlabel('Tiempo (Velas Procesadas)', fontsize=10)
    plt.ylabel('Bankroll (USDC)', fontsize=10)
    plt.grid(True, alpha=0.2)
    plt.fill_between(range(len(historial_capital)), historial_capital, BANKROLL_INICIAL, alpha=0.1, color=color_linea)
    plt.axhline(BANKROLL_INICIAL, color='white', linestyle='--', alpha=0.5, label='Capital Inicial')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_backtest()
