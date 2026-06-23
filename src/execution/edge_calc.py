import logging
from typing import Dict, Optional
from src.config import FEE_EFECTIVA, COLCHON_MODELO, MIN_EDGE_REQUIRED, MAX_PRICE_PAY

# Configuración del Logger
logger = logging.getLogger(__name__)

class EdgeCalculator:
    """
    Motor de evaluación de Ventaja Matemática (Edge).
    Ahora implementa filtros anti-favoritos (Cap de Cuota) y exige Edges gruesos.
    """
    def __init__(self, fee=FEE_EFECTIVA, colchon=COLCHON_MODELO, min_edge=MIN_EDGE_REQUIRED, max_price=MAX_PRICE_PAY):
        self.fee = fee
        self.colchon = colchon
        self.min_edge = min_edge
        self.max_price = max_price

    def evaluate_opportunity(self, prob_yes, orderbook):
        """
        Evalúa si hay una ventaja matemática real, mostrando toda su matemática en consola.
        """
        try:
            best_bid = orderbook.get('bids', [{'price': 0}])[0]['price']
            best_ask = orderbook.get('asks', [{'price': 1}])[0]['price']
            midprice = orderbook.get('midprice', 0.50)
            
            # Determinar el lado con mayor probabilidad teórica
            if prob_yes > 0.50:
                side = "YES"
                p_modelo = prob_yes
                p_mercado = best_ask  # Si compramos YES, pagamos el Ask
            else:
                side = "NO"
                p_modelo = 1.0 - prob_yes
                p_mercado = 1.0 - best_bid  # Si compramos NO, pagamos la inversa del Bid
            
            # Cálculo estricto del Edge
            spread = best_ask - best_bid
            edge_bruto = p_modelo - p_mercado
            edge_neto = edge_bruto - spread - self.fee - self.min_edge

            # --- LOGS DETALLADOS (Radiografía del Guardián) ---
            logger.info("--- Radiografía Matemática (Edge) ---")
            logger.info(f"Lado: {side} | Bid={best_bid:.3f} | Ask={best_ask:.3f} | Mid={midprice:.3f} | Spread={spread:.3f}")
            logger.info(f"P_Modelo={p_modelo:.3f} | P_Mercado (Costo)={p_mercado:.3f}")
            logger.info(f"Edge_Bruto={edge_bruto:.3f} | Edge_Neto={edge_neto:.3f}")

            # Filtros de rechazo con sus motivos exactos
            motivo_no_trade = None
            if p_mercado > self.max_price:
                motivo_no_trade = f"Favorito demasiado caro (Precio {p_mercado:.2f} > Límite {self.max_price:.2f})"
            elif edge_neto <= 0:
                motivo_no_trade = f"Edge Neto Negativo o Insuficiente ({edge_neto:.3f} <= 0)"
            elif spread > 0.10: # Límite de seguridad de spread
                motivo_no_trade = f"Spread demasiado alto ({spread:.3f} > 0.10)"

            if motivo_no_trade:
                logger.info(f"⚖️ RECHAZADO: {motivo_no_trade}")
                return None

            # Si pasa todos los filtros, hay una oportunidad real
            logger.info("✅ ¡OPORTUNIDAD APROBADA!")
            liquidez = orderbook.get('asks', [{'size': 0}])[0]['size'] if side == "YES" else orderbook.get('bids', [{'size': 0}])[0]['size']

            return {
                'side': side,
                'prob_mercado': p_mercado,
                'edge': edge_neto,
                'liquidez_disponible': liquidez
            }

        except Exception as e:
            logger.error(f"Error en EdgeCalculator: {e}")
            return None

        # Lógica de Decisión con Filtro de Precio ("Underdogs") y Edge Mínimo
        if edge_neto_yes >= self.min_edge and midprice_yes <= self.max_price:
            logger.info(f"🚀 GANGA DETECTADA (YES): Precio ${midprice_yes:.2f} | Edge Neto: {edge_neto_yes:.4f}")
            return {
                "side": "YES",
                "edge": edge_neto_yes,
                "prob_mercado": midprice_yes,
                "liquidez_disponible": orderbook['ask_size']
            }
            
        elif edge_neto_no >= self.min_edge and midprice_no <= self.max_price:
            logger.info(f"🩸 MERCADO SOBREVALORADO DETECTADO (Comprar NO): Precio ${midprice_no:.2f} | Edge Neto: {edge_neto_no:.4f}")
            return {
                "side": "NO",
                "edge": edge_neto_no,
                "prob_mercado": midprice_no,
                "liquidez_disponible": orderbook['bid_size'] 
            }
            
        else:
            logger.info("⚖️ Mercado eficiente, favorito demasiado caro o edge insuficiente. NO TRADE.")
            return None
        