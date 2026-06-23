import requests
import logging
import json
from typing import Optional, Dict

# Configuración de un "Logger" para registrar errores profesionalmente
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PolymarketClient:
    """
    Cliente para interactuar con la Gamma API (CLOB) de Polymarket.
    Extrae liquidez y calcula el precio de consenso (Midprice).
    """
    def __init__(self):
        # Endpoint principal de la API pública de Polymarket
        self.base_url = "https://clob.polymarket.com"

    def get_orderbook(self, token_id: str) -> Optional[Dict[str, float]]:
        """
        Descarga el libro de órdenes para un token específico (YES o NO).
        Retorna un diccionario con los precios, el spread y la liquidez.
        """
        url = f"{self.base_url}/book?token_id={token_id}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() # Lanza un error si la API rechaza la conexión
            data = response.json()

            # Protección contra mercados ilíquidos (Libro vacío)
            if not data.get('bids') or not data.get('asks'):
                logger.warning(f"⚠️ Libro de órdenes vacío o ilíquido para el token: {token_id}")
                return None

            # Extracción del Nivel 1 del Order Book (Mejor comprador y vendedor)
            best_bid = float(data['bids'][0]['price'])
            bid_size = float(data['bids'][0]['size'])
            
            best_ask = float(data['asks'][0]['price'])
            ask_size = float(data['asks'][0]['size'])

            # Cálculo del Midprice para evitar sesgos direccionales
            midprice = (best_bid + best_ask) / 2.0
            
            # Cálculo de la fricción inmediata
            spread = best_ask - best_bid

            return {
                "best_bid": best_bid,
                "best_ask": best_ask,
                "bid_size": bid_size,
                "ask_size": ask_size,
                "midprice": midprice,
                "spread": spread
            }

        except requests.exceptions.RequestException as e:
            logger.debug(f"❌ Error de conexión con Polymarket API: {e}")
            return None

    def find_active_btc_token(self) -> Optional[str]:
        """
        Busca un token activo relacionado con BTC/BITCOIN usando la Gamma API.
        Retorna el primer `clobTokenId` encontrado o `None` si no hay resultados.
        """
        url = "https://gamma-api.polymarket.com/events?limit=100&active=true"
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            eventos = response.json()

            for evento in eventos:
                titulo = evento.get('title', '').upper()
                if 'BITCOIN' in titulo or 'BTC' in titulo:
                    mercados = evento.get('markets', [])
                    for mercado in mercados:
                        token_ids_raw = mercado.get('clobTokenIds', '[]')
                        if isinstance(token_ids_raw, str):
                            try:
                                token_ids = json.loads(token_ids_raw)
                            except Exception:
                                token_ids = []
                        else:
                            token_ids = token_ids_raw

                        if token_ids and len(token_ids) >= 1:
                            # Verificamos que el token tenga un orderbook activo
                            for t in token_ids:
                                try:
                                    ob = self.get_orderbook(t)
                                    if ob:
                                        return t
                                except Exception:
                                    continue
        except Exception as e:
            logger.debug(f"No se pudo descubrir token activo BTC: {e}")

        return None

# --- Bloque de Prueba Rápida ---
# Si ejecutas este archivo directamente, probará la conexión.
if __name__ == "__main__":
    cliente = PolymarketClient()
    # Usamos un token_id de ejemplo (Esto cambiará en producción)
    # Nota: Este es un ID ficticio para probar la estructura.
    test_token_id = "21742633143463906290569050155826241533067272736897614950488156847949938836455" 
    
    print("Probando conexión a Polymarket...")
    resultado = cliente.get_orderbook(test_token_id)
    if resultado:
        print(f"✅ Conexión Exitosa. Midprice Actual: ${resultado['midprice']:.4f}")
        print(f"Fricción (Spread): {resultado['spread']:.4f} centavos")
        