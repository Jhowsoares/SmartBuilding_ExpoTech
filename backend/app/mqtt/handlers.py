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


async def _room_slug(db_session, room_id) -> Optional[str]:
    """Deriva o slug MQTT da sala (ex.: 'room-302') a partir do nome.

    Gateway ESP32 e simulador escutam devices/ac/{room_slug}/commands, mas o
    backend identifica salas por UUID. O número está no nome ('Sala 302 - ...').
    """
    import re
    from sqlalchemy import select
    from app.models.room import Room

    room = (await db_session.execute(
        select(Room).where(Room.id == room_id)
    )).scalar_one_or_none()
    if not room:
        return None
    match = re.search(r"\d{3}", room.name or "")
    return f"room-{match.group()}" if match else None


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
                        # Publica via MQTT (UUID + slug da sala p/ gateway/simulador)
                        from app.mqtt.client import mqtt_client
                        mqtt_client.publish_command(str(dev_id), "off")
                        slug = await _room_slug(db_session, device.room_id)
                        if slug:
                            mqtt_client.publish_command(slug, "off")
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
                        slug = await _room_slug(db_session, device.room_id)
                        if slug:
                            mqtt_client.publish_command(slug, "setpoint", action.value)
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
    from app.models.device import DeviceStatus
    from app.repositories.device_repository import DeviceRepository

    # Mapeia tipo de sensor ao tipo de dispositivo correspondente no banco
    _SENSOR_TO_DEVICE_TYPE = {
        "temperature": "temperature_sensor",
        "humidity": "humidity_sensor",
        "presence": "presence_sensor",
        "window": "window_sensor",
    }

    try:
        # Extrai room_id ou device_id do tópico
        # Ex.: sensors/room/{room_id}/temperature
        parts = topic.split("/")
        entity_id = parts[2] if len(parts) > 2 else "unknown"

        value = float(payload.get("value", payload.get("valor", 0)))
        tick = int(payload.get("tick", 0))
        ts_str = payload.get("timestamp")
        ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)

        # Extrai número da sala do entity_id (ex: "room-101" → "101")
        room_num = entity_id.split("-")[-1] if "-" in entity_id else entity_id
        ac_device_id: str | None = None   # UUID do AC real da sala (se existir)

        async with AsyncSessionLocal() as db:
            # ── Atualiza status dos devices dessa sala para ONLINE ────────────
            # Encontra o sensor device correspondente pelo mqtt_topic
            # (compara pela parte do topic que inclui o número da sala)
            try:
                from sqlalchemy import select, or_
                from app.models.device import Device, DeviceType
                from app.models.room import Room

                # Busca salas cujo nome contenha o número da sala
                rooms_q = await db.execute(
                    select(Room).where(Room.name.contains(room_num))
                )
                matching_rooms = rooms_q.scalars().all()

                if matching_rooms:
                    # UUID do AC real da sala → usado como device_id nas regras,
                    # para que alertas/comandos persistam com FK válida.
                    ac_id_row = (await db.execute(
                        select(Device.id).where(
                            Device.room_id == matching_rooms[0].id,
                            Device.device_type == DeviceType.AC,
                        ).limit(1)
                    )).scalar_one_or_none()
                    if ac_id_row is not None:
                        ac_device_id = str(ac_id_row)

                    dev_type_str = _SENSOR_TO_DEVICE_TYPE.get(sensor_type)
                    for room_obj in matching_rooms:
                        # Atualiza o sensor deste tipo para online (quando há um
                        # device correspondente; energia não tem device próprio)
                        from sqlalchemy import update
                        if dev_type_str:
                            await db.execute(
                                update(Device)
                                .where(
                                    Device.room_id == room_obj.id,
                                    Device.device_type == dev_type_str,
                                )
                                .values(
                                    status=DeviceStatus.ONLINE,
                                    last_seen_at=ts,
                                )
                            )
                        # Também marca o AC como online quando há atividade na sala
                        await db.execute(
                            update(Device)
                            .where(
                                Device.room_id == room_obj.id,
                                Device.device_type == DeviceType.AC,
                            )
                            .values(status=DeviceStatus.ONLINE, last_seen_at=ts)
                        )
            except Exception as e:
                logger.debug("Não foi possível atualizar status do device: %s", e)

            # ── Persiste leitura ──────────────────────────────────────────────
            # RN08: Validação básica antes de persistir
            record = SensorData(
                sensor_id=f"sensor-{sensor_type}-{entity_id}",
                tipo=sensor_type,
                valor=value,
                tick=tick,
                timestamp=ts,
                is_anomaly=False,
                received_at=datetime.now(timezone.utc),
            )
            db.add(record)

            # Aplica regras de negócio.
            # Estado é sempre indexado pela sala (entity_id), para ficar
            # consistente com o feedback do AC. As AÇÕES das regras, porém,
            # usam o UUID real do AC para persistirem com FK válida.
            state = _get_state(entity_id)
            device_id = ac_device_id or payload.get("device_id", entity_id)

            # ── Acumula consumo real (kWh) a partir da potência medida ────────
            if sensor_type == "power" and value > 0:
                last_ts = state.get("last_power_ts")
                if last_ts is not None:
                    dt_h = (ts - last_ts).total_seconds() / 3600.0
                    # ignora gaps grandes (reinício/desconexão) > 10 min
                    if 0 < dt_h <= (10 / 60):
                        state["daily_kwh"] = state.get("daily_kwh", 0.0) + (value / 1000.0) * dt_h
                # zera o acumulado quando vira o dia
                if last_ts is None or last_ts.date() != ts.date():
                    state["daily_kwh"] = 0.0
                state["last_power_ts"] = ts

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
        # Grandezas elétricas vindas do gateway ESP32 → Arduino AC
        ("sensors/room/+/power", "power"),
        ("sensors/room/+/voltage", "voltage"),
        ("sensors/room/+/current", "current"),
        ("devices/ac/+/feedback", "feedback"),
    ]

    for topic, sensor_type in subscriptions:
        if sensor_type == "feedback":
            mqtt_client.subscribe(topic, _feedback_callback)
        else:
            mqtt_client.subscribe(topic, _create_mqtt_callback(sensor_type))

    logger.info("MQTT: %d tópicos subscritos.", len(subscriptions))


def _feedback_callback(topic: str, payload: dict) -> None:
    """Processa feedback de dispositivos AC (confirmação de comando).

    Quando vem do gateway ESP32 (hardware real), reflete o estado no BANCO para
    que o frontend mostre o que o AC físico realmente fez.
    """
    loop = _main_event_loop
    if loop is not None and loop.is_running():
        asyncio.run_coroutine_threadsafe(_async_feedback(topic, payload), loop)
    else:
        # Fallback: ao menos atualiza o estado em memória
        parts = topic.split("/")
        device_id = parts[2] if len(parts) > 2 else "unknown"
        state = _get_state(device_id)
        if "power" in payload:
            state["power_on"] = payload["power"] == "on"
        logger.info("Feedback AC (memória) | device=%s payload=%s", device_id, payload)


async def _async_feedback(topic: str, payload: dict) -> None:
    """Atualiza o estado real do AC no banco a partir do feedback MQTT."""
    from sqlalchemy import select, update
    from app.db.database import AsyncSessionLocal
    from app.models.room import Room
    from app.models.device import Device, DeviceType, DeviceStatus

    parts = topic.split("/")
    entity_id = parts[2] if len(parts) > 2 else "unknown"   # ex.: "room-302"
    room_num = entity_id.split("-")[-1] if "-" in entity_id else entity_id

    power_on = payload["power"] == "on" if "power" in payload else None
    setpoint = float(payload["setpoint"]) if "setpoint" in payload else None

    # Estado em memória (usado pelas regras)
    state = _get_state(entity_id)
    if power_on is not None:
        state["power_on"] = power_on
    if setpoint is not None:
        state["current_setpoint"] = setpoint

    try:
        async with AsyncSessionLocal() as db:
            rooms = (await db.execute(
                select(Room).where(Room.name.contains(room_num))
            )).scalars().all()
            now = datetime.now(timezone.utc)
            for room in rooms:
                values = {"status": DeviceStatus.ONLINE, "last_seen_at": now}
                if power_on is not None:
                    values["power_on"] = power_on
                if setpoint is not None:
                    values["setpoint_celsius"] = setpoint
                await db.execute(
                    update(Device)
                    .where(Device.room_id == room.id, Device.device_type == DeviceType.AC)
                    .values(**values)
                )
            await db.commit()
        logger.info("Feedback AC | sala=%s power=%s setpoint=%s (banco atualizado)",
                    entity_id, power_on, setpoint)
    except Exception as exc:
        logger.error("Erro ao processar feedback AC: %s", exc)
