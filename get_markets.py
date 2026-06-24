import os
import sys

# Auto-execute inside the virtual environment if it exists and we aren't already in it
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
venv_python_win = os.path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe')
venv_python_unix = os.path.join(ROOT_DIR, '.venv', 'bin', 'python')
venv_python = venv_python_win if os.path.exists(venv_python_win) else venv_python_unix

if os.path.exists(venv_python) and os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    import subprocess
    sys.exit(subprocess.call([venv_python] + sys.argv))

import requests
import json
import time
from src.api_clients.poly_client import PolymarketClient

# Configure UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass



def buscar_mercados_btc(limit=2000):
    """
    Escanea la Gamma API para eventos/mercados relacionados con BTC/Bitcoin
    y valida los `clobTokenIds` consultando el CLOB de Polymarket.
    """
    print("🔍 Escaneando eventos en Polymarket y validando Order Books en vivo...")

    urls = [
        f"https://gamma-api.polymarket.com/events?limit={limit}&active=true",
        f"https://gamma-api.polymarket.com/events?limit={limit}",
        f"https://gamma-api.polymarket.com/markets?limit={limit}"
    ]

    client = PolymarketClient()
    encontrados = []
    visited_tokens = set()

    for url in urls:
        try:
            resp = requests.get(url, timeout=12)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"⚠️ No se pudo consultar {url}: {e}")
            continue

        items = data if isinstance(data, list) else data.get('events', []) or data.get('markets', []) or []

        for item in items:
            title = (item.get('title') or item.get('name') or '').upper()

            # Buscar en markets dentro del evento, si existen
            markets = item.get('markets') if isinstance(item.get('markets'), list) else [item] if 'clobTokenIds' in item or 'tokenIds' in item else []

            # Filtrar por keywords amplias
            if not any(k in title for k in ('BITCOIN', 'BTC', 'CRYPTO', 'CRYPTOCURRENCY', 'BLOCKCHAIN')):
                # también revisar preguntas o nombres dentro de markets
                found = False
                for m in markets:
                    q = (m.get('question') or m.get('name') or '').upper()
                    if any(k in q for k in ('BITCOIN', 'BTC')):
                        found = True
                        break
                if not found:
                    continue

            for m in markets:
                question = m.get('question') or m.get('name') or title
                token_ids_raw = m.get('clobTokenIds', m.get('tokenIds', []))

                if isinstance(token_ids_raw, str):
                    try:
                        token_ids = json.loads(token_ids_raw)
                    except Exception:
                        token_ids = []
                else:
                    token_ids = token_ids_raw or []

                for t in token_ids:
                    if not t or t in visited_tokens:
                        continue
                    visited_tokens.add(t)

                    ob = client.get_orderbook(t)
                    if ob:
                        bids = ob.get('bids', [])
                        asks = ob.get('asks', [])
                        if bids and asks:
                            best_bid = float(bids[-1]['price'])
                            best_ask = float(asks[-1]['price'])
                            midprice = (best_bid + best_ask) / 2.0
                            spread = best_ask - best_bid
                            encontrados.append({
                                'token': t,
                                'question': question,
                                'midprice': midprice,
                                'spread': spread
                            })

        # breve pausa para no golpear la API
        time.sleep(0.2)

    if not encontrados:
        print('\n⚠️ No se encontraron mercados BTC con orderbook válido en los endpoints consultados.')
    else:
        print('\n' + '='*80)
        print(f"✅ Se encontraron {len(encontrados)} token(s) válidos:")
        for e in encontrados:
            print(f"- Token: {e['token']} | Mercado: {e['question']} | Mid: {e['midprice']} | Spread: {e['spread']}")

    # Devolver la lista de tokens encontrados para uso programático
    return encontrados


if __name__ == '__main__':
    buscar_mercados_btc(limit=2000)
