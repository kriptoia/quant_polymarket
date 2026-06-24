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
                            return token_ids[0]
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
            queries = ["Bitcoin", "BTC"]
            events_by_slug = {}
            
            for q in queries:
                url = f"{self.gamma_url}/public-search?q={q}"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    results = response.json()
                    for e in results.get('events', []):
                        slug = e.get('slug')
                        if slug and slug not in events_by_slug:
                            events_by_slug[slug] = e
            
            for slug, evento in events_by_slug.items():
                titulo = evento.get('title', '')
                mercados = evento.get('markets', [])
                
                for mercado in mercados:
                    if not mercado.get('active') or mercado.get('closed'):
                        continue
                        
                    token_ids_raw = mercado.get('clobTokenIds', '[]')
                    token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                    
                    if token_ids and len(token_ids) >= 2:
                        token_yes = token_ids[0]
                        
                        # EVALUACIÓN DE LÍQUIDEZ EN TIEMPO REAL
                        ob = self.get_orderbook(token_yes)
                        if ob:
                            bids = ob.get('bids', [])
                            asks = ob.get('asks', [])
                            if bids and asks:
                                best_bid = float(bids[-1]['price'])
                                best_ask = float(asks[-1]['price'])
                                spread = best_ask - best_bid
                                
                                # LA REGLA DE ORO DEL QUANT:
                                # Tiene que haber alguien comprando, alguien vendiendo barato, y un spread operable (< 15%)
                                if best_bid > 0.01 and best_ask < 0.99 and spread <= 0.15:
                                    logger.info(f"✅ Mercado Líquido Encontrado: '{titulo}' -> '{mercado.get('question')}'")
                                    logger.info(f"   📊 Bid: {best_bid} | Ask: {best_ask} | Spread: {spread:.3f}")
                                    return token_yes
            
            logger.warning("Radar Quant: Ningún mercado de BTC superó el filtro estricto de liquidez.")
            return None
            
        except Exception as e:
            logger.error(f"Error en el Radar Quant: {e}")
            return None

    def get_market_title_by_token(self, token_id):
        """
        FUNCIÓN AUXILIAR: Busca pasivamente el título del mercado.
        Solo se llama al momento de mandar Telegram.
        """
        try:
            url = f"{self.gamma_url}/events?limit=200&active=true"
            response = self.session.get(url, timeout=10)
            eventos = response.json()
            
            for evento in eventos:
                mercados = evento.get('markets', [])
                for mercado in mercados:
                    token_ids_raw = mercado.get('clobTokenIds', '[]')
                    token_ids = json.loads(token_ids_raw) if isinstance(token_ids_raw, str) else token_ids_raw
                    
                    if isinstance(token_ids, list) and token_id in token_ids:
                        return mercado.get('question', evento.get('title', 'Mercado de Bitcoin'))
            
            return "Título no encontrado en mercados recientes"
        except Exception as e:
            logger.error(f"Error buscando el título para la metadata: {e}")
            return "Error al extraer título"