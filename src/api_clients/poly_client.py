import requests
import json
import logging

logger = logging.getLogger(__name__)

class PolymarketClient:
    def __init__(self):
        """
        Inicializa el cliente para conectarse a las APIs de Polymarket.
        """
        self.clob_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.session = requests.Session()

    def get_orderbook(self, token_id):
        """
        Descarga el libro de órdenes (Orderbook) actual para un token específico.
        """
        try:
            url = f"{self.clob_url}/book?token_id={token_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.error(f"Error al conectar con el Orderbook de Polymarket: {e}")
            return None

    def find_active_btc_token(self):
        """
        Búsqueda básica de un token de Bitcoin activo (Fallback).
        """
        try:
            url = f"{self.gamma_url}/events?limit=100&active=true"
            response = self.session.get(url, timeout=10)
            eventos = response.json()
            
            for evento in eventos:
                titulo = evento.get('title', '')
                if 'Bitcoin' in titulo or 'BTC' in titulo:
                    mercados = evento.get('markets', [])
                    for mercado in mercados:
                        token_ids_raw = mercado.get('clobTokenIds', '[]')
                        token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                        if token_ids and len(token_ids) >= 2:
                            return token_ids[0] # Devuelve el YES del primer mercado que encuentre
            return None
        except Exception as e:
            logger.error(f"Error buscando token básico: {e}")
            return None

    def find_liquid_btc_token(self):
        """
        RADAR QUANT: Escanea Polymarket y devuelve el primer token de Bitcoin 
        que tenga liquidez real y un spread estrecho operable.
        """
        logger.info("Radar Quant: Escaneando Polymarket en busca de liquidez real...")
        
        try:
            url = f"{self.gamma_url}/events?limit=100&active=true"
            response = self.session.get(url, timeout=10)
            eventos = response.json()
            
            for evento in eventos:
                titulo = evento.get('title', '')
                
                # Filtramos eventos de Bitcoin 
                if 'Bitcoin' in titulo or 'BTC' in titulo:
                    mercados = evento.get('markets', [])
                    for mercado in mercados:
                        token_ids_raw = mercado.get('clobTokenIds', '[]')
                        token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                        
                        if token_ids and len(token_ids) >= 2:
                            token_yes = token_ids[0]
                            
                            # EVALUACIÓN DE LÍQUIDEZ EN TIEMPO REAL
                            ob = self.get_orderbook(token_yes)
                            if ob:
                                best_bid = float(ob.get('bids', [{'price': 0}])[0]['price'])
                                best_ask = float(ob.get('asks', [{'price': 1}])[0]['price'])
                                spread = best_ask - best_bid
                                
                                # LA REGLA DE ORO DEL QUANT:
                                # Tiene que haber alguien comprando, alguien vendiendo barato, y un spread operable (< 15%)
                                if best_bid > 0.01 and best_ask < 0.99 and spread <= 0.15:
                                    logger.info(f"✅ Mercado Líquido Encontrado: '{titulo}'")
                                    logger.info(f"   📊 Bid: {best_bid} | Ask: {best_ask} | Spread: {spread:.3f}")
                                    return token_yes
            
            logger.warning("Radar Quant: Ningún mercado de BTC superó el filtro estricto de liquidez.")
            return None
            
        except Exception as e:
            logger.error(f"Error en el Radar Quant: {e}")
            return None
