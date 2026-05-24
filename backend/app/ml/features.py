"""Pipeline de features para o modelo de predição de consumo.

Responsabilidade:
  - Extrair features temporais e de sensor a partir de registros históricos
  - Preparar X (features) e y (target: consumo estimado em kWh)
  - Gerar features para as próximas 24 horas (inferência)
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


# ── Constantes de consumo estimado ──────────────────────────────────────────
_KW_BASE = 1.2         # kW base por AC
_KW_PER_DEGREE = 0.15  # kW extra por °C acima de 24°C
_IDEAL_TEMP = 24.0
_OPERATING_HOURS = list(range(7, 22))  # RN06: horário de funcionamento 07h–21h


def _kwh_from_temp(temp: float, hours: float = 1.0) -> float:
    extra = max(0.0, temp - _IDEAL_TEMP) * _KW_PER_DEGREE
    return (_KW_BASE + extra) * hours


def extract_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Extrai features de um DataFrame com colunas timestamp, valor (temp), sensor_id.

    Features:
        hour, day_of_week, is_weekend, month, temp_lag1h, temp_mean_3h,
        temp_std_3h, is_operating_hours

    Target:
        kwh_estimado (calculado a partir da temperatura média)
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df["timestamp"].dt.month
    df["is_operating_hours"] = df["hour"].isin(_OPERATING_HOURS).astype(int)

    # Lags e rolling stats
    df["temp_lag1h"] = df["valor"].shift(1).fillna(df["valor"].mean())
    df["temp_mean_3h"] = df["valor"].rolling(window=3, min_periods=1).mean()
    df["temp_std_3h"] = df["valor"].rolling(window=3, min_periods=1).std().fillna(0)

    # Target: kWh estimado por hora
    df["kwh_estimado"] = df["valor"].apply(_kwh_from_temp)
    # Zera consumo fora do horário de funcionamento (RN06)
    df.loc[df["is_operating_hours"] == 0, "kwh_estimado"] = 0.0

    feature_cols = [
        "hour", "day_of_week", "is_weekend", "month",
        "temp_lag1h", "temp_mean_3h", "temp_std_3h", "is_operating_hours",
    ]
    X = df[feature_cols].values.astype(float)
    y = df["kwh_estimado"].values.astype(float)
    return X, y


def generate_future_features(base_temp: float = _IDEAL_TEMP,
                              start_hour: Optional[datetime] = None) -> np.ndarray:
    """Gera features para as próximas 24 horas a partir de agora (para inferência)."""
    if start_hour is None:
        start_hour = datetime.now(timezone.utc)

    rows = []
    for h in range(24):
        future = start_hour.replace(
            minute=0, second=0, microsecond=0
        )
        hour = (start_hour.hour + h) % 24
        day_of_week = (start_hour.weekday() + (start_hour.hour + h) // 24) % 7
        is_weekend = 1 if day_of_week >= 5 else 0
        month = start_hour.month
        is_op = 1 if hour in _OPERATING_HOURS else 0

        # Simula variação de temperatura ao longo do dia
        temp_variation = 2.0 * np.sin(np.pi * (hour - 6) / 12)  # pico às 12h
        temp = base_temp + temp_variation

        rows.append([
            hour, day_of_week, is_weekend, month,
            temp,           # temp_lag1h (aprox)
            temp,           # temp_mean_3h (aprox)
            0.5,            # temp_std_3h (aprox)
            is_op,
        ])

    return np.array(rows, dtype=float)
