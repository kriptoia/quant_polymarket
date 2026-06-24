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

# Configure UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Ajustar el path para que Python encuentre nuestra carpeta src
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import logging
logging.basicConfig(level=logging.INFO)

# Importamos nuestro módulo de alertas
from src.notifications.telegram_bot import send_telegram_alert

def probar_conexion():
    print("Enviando mensaje de prueba a Telegram...")
    
    # Construimos un mensaje con formato HTML (igual que en el bot en vivo)
    mensaje_prueba = (
        "🤖 <b>TEST DE CONEXIÓN EXITOSO</b> 🤖\n\n"
        "Si estás leyendo esto en tu celular, significa que tu "
        "Orquestador Quant tiene línea directa contigo y el sistema "
        "de alertas está funcionando al 100%.\n\n"
        "<i>¡El bot está listo para cazar anomalías en Polymarket!</i> 🎯"
    )
    
    # Ejecutamos la función de envío
    send_telegram_alert(mensaje_prueba)
    print("✅ ¡Comando ejecutado! Revisa tu celular.")

if __name__ == "__main__":
    probar_conexion()
    