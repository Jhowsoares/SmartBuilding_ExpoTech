"""Cliente MQTT — conecta ao broker, publica comandos e subscreve telemetria."""
from __future__ import annotations
import json
import logging
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from app.core.config import settings

logger = logging.getLogger(__name__)


class MQTTClient:
    """Cliente MQTT singleton para o backend FastAPI.

    Responsabilidades:
    - Conectar ao broker Mosquitto com reconexão automática
    - Subscrever nos tópicos de telemetria dos sensores
    - Publicar comandos para dispositivos AC
    - Disparar callbacks registrados para processar mensagens recebidas
    """

    def __init__(self) -> None:
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._message_callbacks: dict[str, list[Callable]] = {}

    def connect(self) -> None:
        """Inicializa a conexão com o broker MQTT."""
        client_id = f"smartbuilding-backend-{settings.MQTT_CLIENT_ID}"
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self._client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        try:
            self._client.connect(
                host=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                keepalive=60,
            )
            self._client.loop_start()
            logger.info("MQTT: conectando a %s:%s", settings.MQTT_BROKER, settings.MQTT_PORT)
        except Exception as exc:
            logger.error("MQTT: falha ao conectar: %s", exc)

    def disconnect(self) -> None:
        """Encerra a conexão com o broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTT: desconectado.")

    def publish_command(self, device_id: str, action: str, value: Optional[float] = None) -> None:
        """Publica um comando para um dispositivo AC.

        Tópico: devices/ac/{device_id}/commands
        Payload: {"action": "on|off|setpoint", "value": float|null}
        """
        if not self._connected or not self._client:
            logger.warning("MQTT: tentativa de publish sem conexão ativa.")
            return
        topic = f"devices/ac/{device_id}/commands"
        payload = json.dumps({"action": action, "value": value})
        result = self._client.publish(topic, payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("MQTT: comando publicado | topic=%s payload=%s", topic, payload)
        else:
            logger.error("MQTT: falha ao publicar | rc=%s", result.rc)

    def subscribe(self, topic: str, callback: Callable[[str, dict], None]) -> None:
        """Registra callback para um tópico MQTT."""
        if topic not in self._message_callbacks:
            self._message_callbacks[topic] = []
        self._message_callbacks[topic].append(callback)
        if self._connected and self._client:
            self._client.subscribe(topic, qos=1)
            logger.info("MQTT: subscrito em '%s'", topic)

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Callbacks internos ──────────────────────────────────────────────────

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        if rc == 0:
            self._connected = True
            logger.info("MQTT: conectado ao broker com sucesso.")
            # Re-subscreve em todos os tópicos registrados após reconexão
            # Copia as chaves antes de iterar para evitar RuntimeError de tamanho
            for topic in list(self._message_callbacks.keys()):
                client.subscribe(topic, qos=1)
                logger.info("MQTT: re-subscrito em '%s'", topic)
        else:
            logger.error("MQTT: falha na conexão, rc=%s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata, rc: int) -> None:
        self._connected = False
        if rc != 0:
            logger.warning("MQTT: desconexão inesperada rc=%s. Tentando reconectar...", rc)

    def _on_message(self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage) -> None:
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except Exception:
            payload = {"raw": message.payload.decode("utf-8")}

        logger.debug("MQTT: mensagem recebida | topic=%s payload=%s", topic, payload)

        # Dispara callbacks exatos e wildcards
        for registered_topic, callbacks in self._message_callbacks.items():
            if mqtt.topic_matches_sub(registered_topic, topic):
                for cb in callbacks:
                    try:
                        cb(topic, payload)
                    except Exception as exc:
                        logger.error("MQTT: erro no callback de '%s': %s", topic, exc)


# Instância singleton — importada pelo main.py no startup
mqtt_client = MQTTClient()
