"""Handler MQTT — processa mensagens recebidas e aplica regras de negócio.

Tópicos subscritos:
  sensors/room/+/temperature
  sensors/room/+/humidity
  sensors/room/+/presence
  devices/ac/+/feedback
  devices/ac/+/status

Integração: chamado pelo mqtt_client no startup via subscribe().
Persiste SensorData, aplica BusinessRulesEngine, executa ações resultantes.
"""
from __future__ import annotations
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Loop principal do FastAPI — gravado durante o lifespan do app
# para que os callbacks MQTT (rodando em thread paho) possam submeter
# coroutines ao loop correto sem criar um event loop separado.
_main_event_loop: asyncio.AbstractEventLoop | None = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_event_loop
    _main_event_loop = loop
_device_state: dict = {}


def _get_state(device_id: str) -> dict:
    if device_id not in _device_state:
        _device_state[device_id] = {
            "last_presence_at": None,
            "window_open_since": None,
            "is_manual_override": False,
            "manual_override_at": None,
            "current_setpoint": 24.0,
            "power_on": False,
            "daily_kwh": 0.0,
        }
    return _device_state[device_id]


def mark_manual_override(device_id: str) -> None:
    """Chamado pelo DeviceService quando um operador envia comando manual (RN04)."""
    state = _get_state(device_id)
    state["is_manual_override"] = True
    state["manual_override_at"] = datetime.now(timezone.utc)


async def _apply_actions(actions, db_session) -> None:
    """Executa as ações geradas pelo motor de regras."""
    from app.ml.business_rules import RuleAction
    from app.models.command import Command, CommandType, CommandStatus
    from app.models.alert import Alert, AlertType, AlertSeverity
    from app.repositories.audit_repository import AuditRepository
    from app.repositories.device_repository import DeviceRepository

    audit = AuditRepository(db_session)
    dev_repo = DeviceRepository(db_session)

    for action in actions:
        try:
            if action.action_type == "power_off":
                # Atualiza device no banco
                try:
                    dev_id = uuid.UUID(action.device_id)
                    device = await dev_repo.get_by_id(dev_id)
                    if device:
                        await dev_repo.set_power(device, False)
                        # Persiste o comando
                        cmd = Command(
                            device_id=dev_id, issued_by="rules_engine",
                            command_type=CommandType.POWER_OFF,
                            status=CommandStatus.EXECUTED,
                            executed_at=datetime.now(timezone.utc),
                        )
                        db_session.add(cmd)
                        # Publica via MQTT
                        from app.mqtt.client import mqtt_client
                        mqtt_client.publish_command(str(dev_id), "off")
                except Exception:
                    pass
                await audit.log(
                    action=f"rule_{action.rule}_power_off",
                    user_id="rules_engine",
                    resource=action.device_id,
                    metadata={"message": action.message},
                )

            elif action.action_type == "set_temperature":
                try:
                    dev_id = uuid.UUID(action.device_id)
                    device = await dev_repo.get_by_id(dev_id)
                    if device and action.value:
                        await dev_repo.set_setpoint(device, action.value)
                        cmd = Command(
                            device_id=dev_id, issued_by="rules_engine",
                            command_type=CommandType.SET_TEMPERATURE,
                            value=action.value,
                            status=CommandStatus.EXECUTED,
                            executed_at=datetime.now(timezone.utc),
                        )
                        db_session.add(cmd)
                        state = _get_state(str(dev_id))
                        state["current_setpoint"] = action.value
                        from app.mqtt.client import mqtt_client
                        mqtt_client.publish_command(str(dev_id), "setpoint", action.value)
                except Exception:
                    pass
                await audit.log(
                    action=f"rule_{action.rule}_set_temp",
                    user_id="rules_engine",
                    resource=action.device_id,
                    metadata={"value": action.value, "message": action.message},
                )

            elif action.action_type == "create_alert":
                try:
                    dev_id = uuid.UUID(action.device_id)
                    alert = Alert(
                        device_id=dev_id,
                        alert_type=AlertType[action.alert_type],
                        severity=AlertSeverity[action.alert_severity.upper()],
                        message=action.message,
                    )
                    db_session.add(alert)
                    logger.warning("Alerta criado | rule=%s type=%s msg=%s",
                                   action.rule, action.alert_type, action.message)
                except Exception as e:
                    logger.error("Erro ao criar alerta: %s", e)

            elif action.action_type == "log":
                logger.info("RuleEngine log | rule=%s device=%s msg=%s",
                            action.rule, action.device_id, action.message)

        except Exception as exc:
            logger.error("Erro ao aplicar ação %s: %s", action.action_type, exc)

    await db_session.flush()


def _create_mqtt_callback(sensor_type: str):
    """Factory de callback MQTT para um tipo de sensor."""

    def callback(topic: str, payload: dict) -> None:
        """Callback síncrono chamado pelo paho-mqtt em thread separada.

        Submete o coroutine ao loop principal do FastAPI via
        run_coroutine_threadsafe, garantindo que asyncpg use o pool correto.
        """
        loop = _main_event_loop
        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(
                _async_callback(topic, payload, sensor_type), loop
            )
        else:
            logger.warning("MQTT callback: loop principal não disponível para %s", topic)

    return callback


async def _async_callback(topic: str, payload: dict, sensor_type: str) -> None:
    """Processa mensagem MQTT de forma assíncrona."""
    from app.db.database import AsyncSessionLocal
    from app.ml.business_rules import rules_engine, RuleContext
    from app.models.sensor_data import SensorData
    from app.repositories.device_repository import DeviceRepository

    try:
        # Extrai room_id ou device_id do tópico
        # Ex.: sensors/room/{room_id}/temperature
        parts = topic.split("/")
        entity_id = parts[2] if len(parts) > 2 else "unknown"

        value = float(payload.get("value", payload.get("valor", 0)))
        tick = int(payload.get("tick", 0))
        ts_str = payload.get("timestamp")
        ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            # RN08: Validação básica antes de persistir
            record = SensorData(
                sensor_id=f"sensor-{sensor_type}-{entity_id[:8]}",
                tipo=sensor_type,
                valor=value,
                tick=tick,
                timestamp=ts,
                is_anomaly=False,
                received_at=datetime.now(timezone.utc),
            )
            db.add(record)

            # Aplica regras de negócio
            device_id = payload.get("device_id", entity_id)
            state = _get_state(device_id)

            if sensor_type == "presence":
                if value == 1:
                    state["last_presence_at"] = ts
                elif value == 0 and state["last_presence_at"] is None:
                    state["last_presence_at"] = ts  # primeira leitura de ausência

            if sensor_type == "window":
                if value == 1 and state["window_open_since"] is None:
                    state["window_open_since"] = ts
                elif value == 0:
                    state["window_open_since"] = None

            ctx = RuleContext(
                device_id=device_id,
                room_id=entity_id,
                sensor_type=sensor_type,
                sensor_value=value,
                timestamp=ts,
                last_presence_at=state.get("last_presence_at"),
                window_open_since=state.get("window_open_since"),
                is_manual_override=state.get("is_manual_override", False),
                manual_override_at=state.get("manual_override_at"),
                current_setpoint=state.get("current_setpoint", 24.0),
                power_on=state.get("power_on", False),
                daily_kwh=state.get("daily_kwh", 0.0),
            )
            actions = rules_engine.evaluate(ctx)
            if actions:
                await _apply_actions(actions, db)

            await db.commit()
            logger.debug("MQTT %s processado | topic=%s value=%s", sensor_type, topic, value)

    except Exception as exc:
        logger.error("Erro ao processar MQTT %s: %s", sensor_type, exc)


def register_mqtt_subscriptions() -> None:
    """Registra todos os tópicos MQTT no client."""
    from app.mqtt.client import mqtt_client

    subscriptions = [
        ("sensors/room/+/temperature", "temperature"),
        ("sensors/room/+/humidity", "humidity"),
        ("sensors/room/+/presence", "presence"),
        ("sensors/room/+/window", "window"),
        ("devices/ac/+/feedback", "feedback"),
    ]

    for topic, sensor_type in subscriptions:
        if sensor_type == "feedback":
            mqtt_client.subscribe(topic, _feedback_callback)
        else:
            mqtt_client.subscribe(topic, _create_mqtt_callback(sensor_type))

    logger.info("MQTT: %d tópicos subscritos.", len(subscriptions))


def _feedback_callback(topic: str, payload: dict) -> None:
    """Processa feedback de dispositivos AC (confirmação de comando)."""
    parts = topic.split("/")
    device_id = parts[2] if len(parts) > 2 else "unknown"
    state = _get_state(device_id)

    if "power" in payload:
        state["power_on"] = payload["power"] == "on"
    if "setpoint" in payload:
        state["current_setpoint"] = float(payload["setpoint"])

    logger.info("Feedback AC | device=%s payload=%s", device_id, payload)
