import requests
import logging
from src.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def send_telegram_alert(mensaje: str):
    """
    Envía un mensaje formateado al chat de Telegram configurado.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Credenciales de Telegram faltantes en .env. Saltando alerta.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("📱 Alerta de Telegram enviada exitosamente al celular.")
    except Exception as e:
        logger.error(f"❌ Error al enviar la alerta de Telegram: {e}")
        