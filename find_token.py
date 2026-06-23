import requests
import json
import sys

# Configure UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def buscar_token_diario():
    print("🔍 Conectando directamente a la matriz de Polymarket...")
    queries = ["Bitcoin", "BTC"]
    events_by_slug = {}
    
    for q in queries:
        url = f"https://gamma-api.polymarket.com/public-search?q={q}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                results = response.json()
                events = results.get('events', [])
                for e in events:
                    slug = e.get('slug')
                    if slug and slug not in events_by_slug:
                        events_by_slug[slug] = e
        except Exception as e:
            print(f"Error al conectar para la consulta '{q}': {e}")
            
    print(f"Se encontraron {len(events_by_slug)} eventos únicos en la búsqueda.\n")
    
    active_count = 0
    for slug, event in events_by_slug.items():
        title = event.get('title', '')
        markets = event.get('markets', [])
        
        # Filtramos solo los mercados que estén activos y no cerrados
        active_markets = [m for m in markets if m.get('active') and not m.get('closed')]
        
        if not active_markets:
            continue
            
        active_count += 1
        print(f"\n✅ Evento: {title} (Slug: {slug})")
        print("=" * 80)
        
        for m in active_markets:
            question = m.get('question')
            clob_token_ids = m.get('clobTokenIds')
            
            if isinstance(clob_token_ids, str):
                try:
                    token_ids = json.loads(clob_token_ids)
                except Exception:
                    token_ids = []
            else:
                token_ids = clob_token_ids or []
                
            if len(token_ids) >= 2:
                print(f"🎯 Mercado: {question}")
                print(f"   👉 YES Token ID: {token_ids[0]}")
                print(f"   👉 NO Token ID:  {token_ids[1]}")
                print("-" * 80)
            else:
                print(f"⚠️ Mercado: {question} (No se encontraron tokens CLOB)")
                print("-" * 80)

    if active_count == 0:
        print("\n❌ No se encontraron mercados activos de Bitcoin/BTC en este momento.")

if __name__ == "__main__":
    buscar_token_diario()