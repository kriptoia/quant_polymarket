import logging
from src.config import BANKROLL_INICIAL, KELLY_CAP, KELLY_FRACTION

# Configuración del Logger
logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Calculadora de tamaño de posición (Position Sizing).
    Utiliza una versión fraccional y limitada del Criterio de Kelly para 
    maximizar el crecimiento del capital sin riesgo de ruina.
    """
    def __init__(self, kelly_cap=KELLY_CAP, kelly_fraction=KELLY_FRACTION):
        self.kelly_cap = kelly_cap
        self.kelly_fraction = kelly_fraction

    def calculate_size(self, edge_neto: float, prob_mercado: float, liquidez_disponible: float, bankroll: float = BANKROLL_INICIAL) -> float:
        """
        Calcula el tamaño exacto en dólares para la orden.
        
        :param edge_neto: La ventaja matemática (Ya descontando fees y spread).
        :param prob_mercado: El precio al que vamos a comprar (ej. 0.60 para YES).
        :param liquidez_disponible: El tamaño máximo que podemos comprar a ese precio.
        :param bankroll: Tu capital total actual.
        :return: Tamaño en dólares a ejecutar.
        """
        logger.info("Calculando dimensionamiento de posición (Criterio de Kelly)...")

        if edge_neto <= 0:
            logger.warning("Intento de calcular tamaño con Edge negativo o nulo. Tamaño de orden: $0.0")
            return 0.0

        # ---------------------------------------------------------
        # 1. Fórmula de Kelly Clásica para Mercados de Predicción
        # Kelly = Edge / Probabilidad de Perder en el Mercado
        # ---------------------------------------------------------
        prob_perder = 1.0 - prob_mercado
        
        # Protección por si la probabilidad de perder es anómalamente cero
        if prob_perder <= 0.0:
            return 0.0

        kelly_completo = edge_neto / prob_perder
        
        # ---------------------------------------------------------
        # 2. Kelly Fraccional (Reducción de volatilidad)
        # ---------------------------------------------------------
        kelly_ajustado = kelly_completo * self.kelly_fraction
        
        # ---------------------------------------------------------
        # 3. Límite de Riesgo Máximo (Cap de la cuenta)
        # ---------------------------------------------------------
        kelly_final = min(kelly_ajustado, self.kelly_cap)
        
        # ---------------------------------------------------------
        # 4. Cálculo Teórico vs. Realidad del Libro de Órdenes
        # ---------------------------------------------------------
        tamaño_teorico = bankroll * kelly_final
        
        # Filtro vital: Nunca comprar más de lo que hay en el nivel actual del libro
        # para evitar el Slippage (deslizamiento de precio)
        tamaño_real = min(tamaño_teorico, liquidez_disponible)
        
        logger.info(f"Kelly Completo: {kelly_completo*100:.2f}% | Kelly Defensivo: {kelly_final*100:.2f}%")
        logger.info(f"Tamaño Teórico: ${tamaño_teorico:.2f} | Liquidez Book: ${liquidez_disponible:.2f}")
        logger.info(f"✅ Tamaño Final de la Orden: ${tamaño_real:.2f} USDC")
        
        return tamaño_real

# --- Bloque de Prueba Rápida ---
if __name__ == "__main__":
    print("Probando Calculadora de Riesgo (Kelly)...")
    sizer = PositionSizer()
    
    # Imaginemos los datos que nos arrojó el edge_calc.py en el paso anterior:
    resultado_oportunidad = {
        "side": "YES",
        "edge": 0.05,            # Un Edge neto del 5%
        "prob_mercado": 0.65,    # Compramos la acción a 65 centavos
        "liquidez_disponible": 150.0 
    }
    
    bankroll_prueba = 10000.0 # Simulamos que tienes $10,000 en la cuenta
    
    tamaño_inversion = sizer.calculate_size(
        edge_neto=resultado_oportunidad["edge"],
        prob_mercado=resultado_oportunidad["prob_mercado"],
        liquidez_disponible=resultado_oportunidad["liquidez_disponible"],
        bankroll=bankroll_prueba
    )
    