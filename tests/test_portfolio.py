import unittest
import time
import os
import csv
import shutil
from src.execution.portfolio_manager import PortfolioManager
from src.execution.trade_logger import log_trade_to_csv
from src.config import DATA_DIR

class TestPortfolioManager(unittest.TestCase):
    def test_cooldown_limit(self):
        # Inicializamos el gestor con 100 USDC de capital
        manager = PortfolioManager(bankroll_inicial=100.0)
        token = "test_token_cooldown_123"
        
        # Al inicio la operación debe ser permitida
        allowed, reason = manager.can_enter_market(token, 0.05, 5.0)
        self.assertTrue(allowed, f"Debería permitir la primera entrada. Razón: {reason}")
        
        # Registramos la entrada
        manager.register_entry(token, 5.0, 0.05)
        
        # Intentamos otra vez inmediatamente -> bloqueado por cooldown
        allowed, reason = manager.can_enter_market(token, 0.05, 5.0)
        self.assertFalse(allowed, "Debería bloquear la segunda entrada por cooldown")
        self.assertIn("cooldown", reason.lower())
        
        # Un token diferente sí debería permitirse
        allowed, reason = manager.can_enter_market("different_token_456", 0.05, 5.0)
        self.assertTrue(allowed, "Debería permitir operar un token diferente")

    def test_daily_limit(self):
        manager = PortfolioManager(bankroll_inicial=100.0)
        
        # Registramos 3 entradas para tokens diferentes
        manager.register_entry("t1", 5.0, 0.05)
        manager.register_entry("t2", 5.0, 0.05)
        manager.register_entry("t3", 5.0, 0.05)
        
        # Una 4ta entrada hoy (últimas 24h) debe ser bloqueada
        allowed, reason = manager.can_enter_market("t4", 0.05, 5.0)
        self.assertFalse(allowed, "Debería bloquear la cuarta entrada por límite diario")
        self.assertIn("límite", reason.lower())

    def test_capital_limit(self):
        manager = PortfolioManager(bankroll_inicial=100.0)
        
        # El 10% de 100 es 10 USDC. Una entrada de 11.0 USDC debe ser rechazada
        allowed, reason = manager.can_enter_market("t1", 0.05, 11.0)
        self.assertFalse(allowed, "Debería bloquear un trade que excede el 10% del capital")
        self.assertIn("supera", reason.lower())
        
        # Una entrada de 10.0 USDC o menos debe ser permitida
        allowed, reason = manager.can_enter_market("t1", 0.05, 10.0)
        self.assertTrue(allowed, "Debería permitir un trade de exactamente 10% del capital")
        
        # Un chequeo pasivo (tamaño = 0) no debe evaluarse contra el límite del 10%
        allowed, reason = manager.can_enter_market("t1", 0.05, 0.0)
        self.assertTrue(allowed, "Un chequeo pasivo de tamaño 0 siempre debe permitirse")

class TestTradeLogger(unittest.TestCase):
    def test_logging(self):
        csv_path = os.path.join(DATA_DIR, "trades.csv")
        
        # Hacemos backup del archivo real de trades si es que existe
        backup_path = csv_path + ".bak"
        has_backup = False
        if os.path.exists(csv_path):
            shutil.move(csv_path, backup_path)
            has_backup = True
            
        try:
            log_trade_to_csv(
                mercado="BTC superior a 100k",
                token_id="test_token_logging",
                side="YES",
                prob_modelo=0.75,
                prob_mercado=0.60,
                edge_neto=0.15,
                inversion=8.50
            )
            
            self.assertTrue(os.path.exists(csv_path), "El archivo CSV no fue creado")
            
            with open(csv_path, mode="r", newline="", encoding="utf-8") as f:
                reader = list(csv.reader(f))
                self.assertEqual(len(reader), 2, "Deberían haber 2 filas: cabecera y el registro")
                self.assertEqual(reader[0][1], "mercado")
                self.assertEqual(reader[1][1], "BTC superior a 100k")
                self.assertEqual(reader[1][2], "test_token_logging")
                self.assertEqual(reader[1][3], "YES")
                self.assertEqual(reader[1][4], "0.7500")
                self.assertEqual(reader[1][5], "0.6000")
                self.assertEqual(reader[1][6], "0.1500")
                self.assertEqual(reader[1][7], "8.50")
        finally:
            # Limpiamos nuestro archivo de prueba y restauramos el backup si existía
            if os.path.exists(csv_path):
                os.remove(csv_path)
            if has_backup:
                shutil.move(backup_path, csv_path)

if __name__ == "__main__":
    unittest.main()
