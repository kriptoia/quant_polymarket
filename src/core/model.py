import pandas as pd
import xgboost as xgb
import logging
from sklearn.metrics import log_loss, accuracy_score

logger = logging.getLogger(__name__)

class PolymarketModel:
    def __init__(self):
        """
        Inicializa el motor predictivo basado en Gradient Boosting.
        """
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )

    def train(self, df):
        """
        Entrena el modelo con el histórico de contratos sintéticos.
        """
        try:
            if 'target' not in df.columns:
                logger.error("Error: No se encontró la columna 'target' en el DataFrame de entrenamiento.")
                return

            # Separamos las variables (Features) de la respuesta correcta (Target)
            X = df.drop(columns=['target'])
            y = df['target']

            # Entrenamos la IA
            self.model.fit(X, y)

            # Calculamos métricas base para el log de la consola
            y_pred = self.model.predict(X)
            y_proba = self.model.predict_proba(X)

            loss = log_loss(y, y_proba)
            acc = accuracy_score(y, y_pred)

            logger.info("✅ Entrenamiento completado.")
            logger.info(f"📊 Calidad Probabilística (Log Loss): {loss:.4f} (Más cerca de 0 es mejor)")
            logger.info(f"🎯 Accuracy Direccional Base: {acc*100:.2f}%")

        except Exception as e:
            logger.error(f"Error crítico durante el entrenamiento: {e}")

    def predict_probability(self, df):
        """
        Predice la probabilidad de que el evento sea YES (1)
        usando EXCLUSIVAMENTE la última vela de datos.
        """
        try:
            # Eliminamos la columna 'target' si existe para que no confunda a XGBoost
            X = df.drop(columns=['target'], errors='ignore')
            
            # Tomamos EXCLUSIVAMENTE la última fila (el momento presente)
            X_latest = X.tail(1)
            
            # predict_proba devuelve una matriz [[prob_clase_0, prob_clase_1]]
            # Queremos la probabilidad de la clase 1 (YES)
            proba = self.model.predict_proba(X_latest)[0, 1]
            
            return float(proba)
        except Exception as e:
            logger.error(f"Error al predecir probabilidad: {e}")
            # Si hay un error, devolvemos un 0.50 neutral para no forzar trades ciegos
            return 0.50
            