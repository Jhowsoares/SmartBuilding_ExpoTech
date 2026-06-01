"""Constantes de ciclo de vida da API — depreciação e sunset (Critério 5)."""

from __future__ import annotations

# Rota legada GET /api/v1/sensors/{sensor_id}/data — ver docs/sistema/deprecation-policy.md
SENSOR_HISTORY_DEPRECATION = 'date="2027-01-01"'
SENSOR_HISTORY_SUNSET = 'date="2027-06-01"'

DEPRECATION_HEADERS = {
    "Deprecation": SENSOR_HISTORY_DEPRECATION,
    "Sunset": SENSOR_HISTORY_SUNSET,
}
