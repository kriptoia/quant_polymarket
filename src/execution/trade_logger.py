import os
import csv
import logging
from datetime import datetime
from src.config import DATA_DIR

# Configuración del Logger
logger = logging.getLogger(__name__)

def log_trade_to_csv(
    mercado: str, 
    token_id: str, 
    side: str, 
    prob_modelo: float, 
    prob_mercado: float, 
    edge_neto: float, 
    inversion: float
):
    """
    Guarda el registro de una operación simulada (paper trade) en el archivo data/trades.csv.
    Crea el archivo y escribe el encabezado si aún no existe.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, "trades.csv")
    
    file_exists = os.path.exists(csv_path)
    
    headers = [
        "timestamp",
        "mercado",
        "token_id",
        "side",
        "prob_modelo",
        "prob_mercado",
        "edge_neto",
        "inversion"
    ]
    
    try:
        with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                timestamp,
                mercado,
                token_id,
                side,
                f"{prob_modelo:.4f}",
                f"{prob_mercado:.4f}",
                f"{edge_neto:.4f}",
                f"{inversion:.2f}"
            ])
        logger.info(f"💾 Operación registrada con éxito en CSV: {csv_path}")
    except Exception as e:
        logger.error(f"⚠️ Error al escribir en el log CSV ({csv_path}): {e}")
