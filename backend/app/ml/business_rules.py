"""Regras de negócio RN01-RN10 — Smart Building HVAC.

Cada função recebe o contexto necessário e aplica a regra,
retornando uma lista de ações a serem executadas (comandos, alertas, logs).

Integração: chamadas a partir do callback MQTT (b10_mqtt_handler.py)
e do serviço de devices.

RN01: Desligamento automático após 15 min sem presença
RN02: Bloqueio com janela aberta por > 5 min
RN03: Temperatura ideal: 23-25°C (faixa recomendada)
RN04: Comandos manuais sobrescrevem automáticos (prioridade manual por 30 min)
RN05: Alerta se consumo > limite configurado
RN06: Respeitar horários de funcionamento (07h-21h)
RN07: Treinar IA diariamente com novos dados
RN08: Validar dados antes de armazenar (anomalias)
RN09: Auditoria completa de ações
RN10: Priorizar eficiência energética
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Configurações das regras ────────────────────────────────────────────────
_ABSENCE_TIMEOUT_MIN = 15          # RN01: minutos sem presença → desligar AC
_WINDOW_BLOCK_MIN = 5              # RN02: minutos com janela aberta → bloquear AC
_IDEAL_TEMP_MIN = 23.0             # RN03: mínimo conforto
_IDEAL_TEMP_MAX = 25.0             # RN03: máximo conforto
_SETPOINT_HARD_MIN = 16.0          # limite absoluto de setpoint
_SETPOINT_HARD_MAX = 30.0          # limite absoluto de setpoint
_MANUAL_OVERRIDE_MIN = 30          # RN04: duração do override manual (min)
_CONSUMPTION_ALERT_KWH = 50.0      # RN05: limite diário de kWh por dispositivo
_OPERATING_START = 7               # RN06: início do horário de funcionamento
_OPERATING_END = 21                # RN06: fim do horário de funcionamento
_TEMP_ANOMALY_MIN = 5.0            # RN08: temperatura mínima válida
_TEMP_ANOMALY_MAX = 55.0           # RN08: temperatura máxima válida
_HUMIDITY_ANOMALY_MIN = 5.0        # RN08: umidade mínima válida
_HUMIDITY_ANOMALY_MAX = 100.0      # RN08: umidade máxima válida


@dataclass
class RuleContext:
    """Contexto passado para as regras."""
    device_id: str
    room_id: str
    sensor_type: str             # temperature | humidity | presence | window
    sensor_value: float
    timestamp: datetime
    last_presence_at: Optional[datetime] = None
    window_open_since: Optional[datetime] = None
    is_manual_override: bool = False
    manual_override_at: Optional[datetime] = None
    current_setpoint: float = 24.0
    power_on: bool = False
    daily_kwh: float = 0.0
    extra: Dict = field(default_factory=dict)


@dataclass
class RuleAction:
    """Ação resultante de uma regra."""
    rule: str
    action_type: str   # power_off | set_temperature | create_alert | log
    device_id: str
    value: Optional[float] = None
    alert_type: Optional[str] = None
    alert_severity: Optional[str] = None
    message: str = ""


class BusinessRulesEngine:
    """Motor de regras de negócio — avalia todas as regras para um evento."""

    def evaluate(self, ctx: RuleContext) -> List[RuleAction]:
        actions: List[RuleAction] = []
        now = ctx.timestamp or datetime.now(timezone.utc)

        # RN08: Validar dados PRIMEIRO
        if not self._rn08_validate(ctx):
            actions.append(RuleAction(
                rule="RN08", action_type="log", device_id=ctx.device_id,
                message=f"Leitura inválida descartada: {ctx.sensor_type}={ctx.sensor_value}",
            ))
            return actions  # não processa mais se dado inválido

        # RN06: Horário de funcionamento
        if not self._rn06_is_operating_hours(now):
            if ctx.power_on:
                actions.append(RuleAction(
                    rule="RN06", action_type="power_off", device_id=ctx.device_id,
                    message=f"Desligamento por fora do horário ({now.hour}h). "
                            f"Funcionamento: {_OPERATING_START}h–{_OPERATING_END}h.",
                ))
            return actions  # fora do horário: nenhuma outra regra se aplica

        # RN04: Override manual tem prioridade (ignora automações por 30 min)
        if ctx.is_manual_override and ctx.manual_override_at:
            override_age = (now - ctx.manual_override_at).total_seconds() / 60
            if override_age < _MANUAL_OVERRIDE_MIN:
                logger.debug("RN04: override manual ativo (%d min restantes).",
                             int(_MANUAL_OVERRIDE_MIN - override_age))
                return actions  # respeita o override

        # RN01: Ausência prolongada → desligar AC
        if ctx.sensor_type == "presence" and ctx.sensor_value == 0:
            if ctx.last_presence_at:
                absent_min = (now - ctx.last_presence_at).total_seconds() / 60
                if absent_min >= _ABSENCE_TIMEOUT_MIN and ctx.power_on:
                    actions.append(RuleAction(
                        rule="RN01", action_type="power_off", device_id=ctx.device_id,
                        message=f"Desligamento automático após {int(absent_min)} min sem presença.",
                    ))

        # RN02: Janela aberta → bloquear AC e criar alerta
        if ctx.sensor_type == "window" and ctx.sensor_value == 1:  # 1 = aberta
            if ctx.window_open_since:
                window_min = (now - ctx.window_open_since).total_seconds() / 60
                if window_min >= _WINDOW_BLOCK_MIN:
                    if ctx.power_on:
                        actions.append(RuleAction(
                            rule="RN02", action_type="power_off", device_id=ctx.device_id,
                            message=f"AC desligado: janela aberta há {int(window_min)} min.",
                        ))
                    actions.append(RuleAction(
                        rule="RN02", action_type="create_alert",
                        device_id=ctx.device_id,
                        alert_type="WINDOW_OPEN", alert_severity="warning",
                        message=f"Janela aberta há {int(window_min)} min com AC ligado.",
                    ))

        # RN03 + RN10: Temperatura fora da faixa ideal → ajustar setpoint
        if ctx.sensor_type == "temperature" and ctx.power_on:
            if ctx.sensor_value > _IDEAL_TEMP_MAX + 2:
                new_set = max(_SETPOINT_HARD_MIN, min(_IDEAL_TEMP_MAX, ctx.current_setpoint - 1.0))
                if new_set != ctx.current_setpoint:
                    actions.append(RuleAction(
                        rule="RN03+RN10", action_type="set_temperature",
                        device_id=ctx.device_id, value=new_set,
                        message=f"Setpoint ajustado para {new_set}°C (temp. ambiente: {ctx.sensor_value:.1f}°C).",
                    ))
                # Alerta de temperatura alta
                if ctx.sensor_value > 35.0:
                    actions.append(RuleAction(
                        rule="RN03", action_type="create_alert",
                        device_id=ctx.device_id,
                        alert_type="HIGH_TEMPERATURE", alert_severity="critical",
                        message=f"Temperatura crítica: {ctx.sensor_value:.1f}°C.",
                    ))
                elif ctx.sensor_value > 30.0:
                    actions.append(RuleAction(
                        rule="RN03", action_type="create_alert",
                        device_id=ctx.device_id,
                        alert_type="HIGH_TEMPERATURE", alert_severity="warning",
                        message=f"Temperatura elevada: {ctx.sensor_value:.1f}°C.",
                    ))

        # RN05: Alerta de consumo excessivo
        if ctx.daily_kwh >= _CONSUMPTION_ALERT_KWH:
            actions.append(RuleAction(
                rule="RN05", action_type="create_alert",
                device_id=ctx.device_id,
                alert_type="CONSUMPTION_LIMIT", alert_severity="warning",
                message=f"Consumo diário atingiu {ctx.daily_kwh:.1f} kWh (limite: {_CONSUMPTION_ALERT_KWH} kWh).",
            ))

        return actions

    @staticmethod
    def _rn06_is_operating_hours(now: datetime) -> bool:
        """RN06: retorna True se estiver dentro do horário de funcionamento."""
        return _OPERATING_START <= now.hour < _OPERATING_END

    @staticmethod
    def _rn08_validate(ctx: RuleContext) -> bool:
        """RN08: valida limites físicos do sensor."""
        if ctx.sensor_type == "temperature":
            return _TEMP_ANOMALY_MIN <= ctx.sensor_value <= _TEMP_ANOMALY_MAX
        if ctx.sensor_type == "humidity":
            return _HUMIDITY_ANOMALY_MIN <= ctx.sensor_value <= _HUMIDITY_ANOMALY_MAX
        if ctx.sensor_type in ("presence", "window"):
            return ctx.sensor_value in (0, 1)
        return True


# Singleton
rules_engine = BusinessRulesEngine()
