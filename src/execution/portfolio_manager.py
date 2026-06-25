import time
import logging

# Configuración del Logger
logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Jefe de Riesgos y Administrador de Portafolio.
    Enfuerza reglas de control de riesgos y limites operativos:
    - Cooldown de 60 minutos por token.
    - Máximo 3 entradas al día (últimas 24 horas) a nivel global.
    - Máximo 10% de capital por entrada individual.
    """
    def __init__(self, bankroll_inicial: float):
        self.bankroll_inicial = bankroll_inicial
        self.current_bankroll = bankroll_inicial
        # Lista de diccionarios para guardar entradas:
        # {'timestamp': float, 'token_id': str, 'size': float, 'edge': float}
        self.entries = []
        logger.info(f"💼 PortfolioManager inicializado con capital de ${self.bankroll_inicial:.2f} USDC")

    def can_enter_market(self, token_id: str, edge: float, size: float) -> tuple[bool, str]:
        """
        Evalúa si la operación propuesta cumple con las políticas de riesgo.
        
        :param token_id: El identificador único del token/mercado.
        :param edge: La ventaja matemática calculada para este trade.
        :param size: El tamaño de la inversión en USDC.
        :return: Tupla (permitido: bool, razon: str)
        """
        now = time.time()

        # 1. Regla de Cooldown: 60 minutos por token
        token_entries = [e for e in self.entries if e['token_id'] == token_id]
        if token_entries:
            last_entry_time = max(e['timestamp'] for e in token_entries)
            elapsed = now - last_entry_time
            if elapsed < 3600:
                remaining_seconds = 3600 - elapsed
                remaining_minutes = remaining_seconds / 60
                return False, f"cooldown activo para {token_id[:15]}... (faltan {remaining_minutes:.1f} min)"

        # 2. Regla de Operaciones Máximas: Máximo 3 entradas al día (últimas 24 horas)
        day_entries = [e for e in self.entries if now - e['timestamp'] < 86400]
        if len(day_entries) >= 3:
            return False, f"límite diario alcanzado (3 entradas en las últimas 24 horas)"

        # 3. Regla de Capital Máximo: Máximo 10% de capital por trade
        # Solo se verifica si el tamaño es mayor a 0 (evitando bloquear chequeos pasivos)
        if size > 0:
            max_size = 0.10 * self.current_bankroll
            if size > max_size:
                return False, f"tamaño de trade (${size:.2f}) supera el 10% del capital (${max_size:.2f})"

        return True, "Operación permitida bajo los parámetros de riesgo"

    def register_entry(self, token_id: str, size: float, edge: float):
        """
        Registra una entrada en el historial de operaciones de control.
        
        :param token_id: El identificador del token/mercado operado.
        :param size: Tamaño de la orden ejecutada en USDC.
        :param edge: Ventaja matemática al momento del trade.
        """
        now = time.time()
        self.entries.append({
            'timestamp': now,
            'token_id': token_id,
            'size': size,
            'edge': edge
        })
        logger.info(
            f"📥 Entrada registrada en memoria de Portfolio Manager: "
            f"Token={token_id[:15]}..., Tamaño=${size:.2f} USDC, Edge={edge*100:.2f}%"
        )
