import logging

logger = logging.getLogger(__name__)

class EdgeCalculator:
    def __init__(self, umbral_edge_minimo=0.05, max_costo_favorito=0.60):
        """
        umbral_edge_minimo: Ventaja matemática neta mínima para operar (ej. 5%)
        max_costo_favorito: Precio máximo a pagar. Si cuesta > 0.60 (60c), es muy caro.
        """
        self.umbral_edge_minimo = umbral_edge_minimo
        self.max_costo_favorito = max_costo_favorito

    def evaluate_opportunity(self, prob_yes, orderbook):
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        if not bids or not asks:
            return None
            
        # Extraemos precios base del lado YES del Orderbook
        best_bid_yes = float(bids[-1]['price'])
        best_ask_yes = float(asks[-1]['price'])
        
        # Matemáticas de Complementos de Polymarket
        # Comprar YES cuesta el Ask de YES
        # Comprar NO cuesta (1 - Bid de YES)
        costo_yes = best_ask_yes
        costo_no = 1.0 - best_bid_yes
        
        # Probabilidades enfrentadas del Modelo
        prob_no = 1.0 - prob_yes
        
        # Calculamos la ventaja (Edge) de cada lado
        edge_yes = prob_yes - costo_yes
        edge_no = prob_no - costo_no
        
        # --- IMPRESIÓN CLARA Y TRANSPARENTE (Telemetría Quant) ---
        logger.info("--- Radiografía Matemática (Edge) ---")
        logger.info(f"P_Yes_Modelo = {prob_yes:.3f} | P_No_Modelo = {prob_no:.3f}")
        logger.info(f"Costo_Yes = {costo_yes:.3f} | Costo_No = {costo_no:.3f}")
        
        # El bot elige el lado que tenga el mayor Edge
        if edge_no > edge_yes:
            lado_evaluado = "NO"
            prob_modelo_eval = prob_no
            costo_eval = costo_no
            edge_eval = edge_no
            # La liquidez de NO es el volumen pujando por YES
            liquidez = float(bids[-1].get('size', 0))
        else:
            lado_evaluado = "YES"
            prob_modelo_eval = prob_yes
            costo_eval = costo_yes
            edge_eval = edge_yes
            # La liquidez de YES es el volumen ofreciendo YES
            liquidez = float(asks[-1].get('size', 0))

        # Imprimir el cálculo matemático del Lado Ganador
        logger.info(f"Lado evaluado = {lado_evaluado}")
        logger.info(f"Edge_Bruto_{lado_evaluado} = {prob_modelo_eval:.3f} - {costo_eval:.3f} = {edge_eval:.3f}")
        
        # 1er Filtro: No comprar favoritos demasiado caros
        if costo_eval > self.max_costo_favorito:
            logger.info(f"⚖️ RECHAZADO: Favorito demasiado caro (Precio {costo_eval:.2f} > Límite {self.max_costo_favorito:.2f})")
            return None
            
        # Cálculo del Edge Neto asumiendo el spread (deslizamiento)
        spread = best_ask_yes - best_bid_yes
        edge_neto = edge_eval - spread
        
        # 2do Filtro: ¿El Edge Neto vale la pena?
        if edge_neto >= self.umbral_edge_minimo:
            logger.info(f"✅ Edge Neto ({edge_neto:.3f}) superó umbral. ¡OPORTUNIDAD APROBADA!")
            return {
                'side': lado_evaluado,
                'prob_modelo': prob_modelo_eval,
                'prob_mercado': costo_eval,
                'edge': edge_neto,
                'liquidez_disponible': liquidez
            }
            
        return None