"""Modelo de predição de consumo energético (scikit-learn).

Fluxo:
  1. Carregar histórico de sensor_data (temperatura)
  2. Extrair features via ml/features.py
  3. Treinar RandomForest ou LinearRegression
  4. Persistir modelo em disco (joblib)
  5. Expor predict_24h() para o endpoint /predictions/24h

Retreinamento: agendado para rodar às 02:00 via BackgroundTasks ou CRON.
"""
from __future__ import annotations
import logging
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from app.ml.features import extract_features, generate_future_features, _IDEAL_TEMP

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(__file__).parent / "models"
_MODEL_PATH = _MODEL_DIR / "consumption_model.pkl"
_SCALER_PATH = _MODEL_DIR / "scaler.pkl"


def _ensure_dir() -> None:
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)


class ConsumptionPredictor:
    """Preditor de consumo energético para as próximas 24 horas."""

    def __init__(self) -> None:
        self.model = None
        self.scaler = None
        self.model_version: str = "untrained"
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        try:
            if _MODEL_PATH.exists() and _SCALER_PATH.exists():
                with open(_MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(_SCALER_PATH, "rb") as f:
                    self.scaler = pickle.load(f)
                self.model_version = _MODEL_PATH.stat().st_mtime.__str__()
                logger.info("Modelo de predição carregado de %s", _MODEL_PATH)
        except Exception as exc:
            logger.warning("Não foi possível carregar modelo salvo: %s", exc)

    def train(self, records: List[dict]) -> dict:
        """Treina o modelo com registros históricos.

        Args:
            records: lista de dicts com campos timestamp, valor, sensor_id

        Returns:
            dict com métricas (MAE, R²)
        """
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score

        if len(records) < 10:
            logger.warning("Dados insuficientes para treino (%d registros). Usando modelo sintético.", len(records))
            return self._train_synthetic()

        df = pd.DataFrame(records)
        X, y = extract_features(df)

        if len(X) < 5:
            return self._train_synthetic()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model.fit(X_train_scaled, y_train)

        y_pred = model.predict(X_test_scaled)
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        self.model = model
        self.scaler = scaler
        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._save()

        metrics = {"mae": round(mae, 4), "r2": round(r2, 4),
                   "n_samples": len(records), "model_version": self.model_version}
        logger.info("Modelo treinado | MAE=%.4f R²=%.4f n=%d", mae, r2, len(records))
        return metrics

    def _train_synthetic(self) -> dict:
        """Treina com dados sintéticos para garantir que o modelo existe."""
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        import random

        logger.info("Treinando com dados sintéticos (sem histórico real suficiente).")
        # Gera 7 dias de dados sintéticos (168 horas)
        rows = []
        base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        for h in range(168):
            hour = h % 24
            temp = 22.0 + 4.0 * abs(np.sin(np.pi * hour / 12)) + random.gauss(0, 0.5)
            rows.append({"timestamp": base.replace(hour=hour), "valor": temp, "sensor_id": "synth"})

        df = pd.DataFrame(rows)
        X, y = extract_features(df)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = LinearRegression()
        model.fit(X_scaled, y)

        self.model = model
        self.scaler = scaler
        self.model_version = "synthetic_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._save()
        return {"mae": 0.0, "r2": 0.0, "n_samples": 168, "model_version": self.model_version, "synthetic": True}

    def predict_24h(self, base_temp: float = _IDEAL_TEMP) -> List[dict]:
        """Retorna predição de consumo para as próximas 24 horas."""
        if self.model is None or self.scaler is None:
            self._train_synthetic()

        X_future = generate_future_features(base_temp=base_temp)
        X_scaled = self.scaler.transform(X_future)
        y_pred = self.model.predict(X_scaled)

        now = datetime.now(timezone.utc)
        predictions = []
        for h, kwh in enumerate(y_pred):
            kwh_val = max(0.0, float(kwh))
            hour = (now.hour + h) % 24
            is_op = hour in range(7, 22)
            predictions.append({
                "hora": h,
                "hour_of_day": hour,
                "kwh_previsto": round(kwh_val, 3),
                "is_operating_hour": is_op,
                "confidence": 0.82 if not self.model_version.startswith("synthetic") else 0.55,
            })
        return predictions

    def _save(self) -> None:
        _ensure_dir()
        with open(_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        with open(_SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Modelo salvo em %s", _MODEL_PATH)

    def is_trained(self) -> bool:
        return self.model is not None


# Singleton
predictor = ConsumptionPredictor()
