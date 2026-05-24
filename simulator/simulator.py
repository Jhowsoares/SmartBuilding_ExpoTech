"""
Simulador MQTT — Smart Building
Simula 14 salas publicando temperatura, umidade e presença a cada 5 segundos.

Tópicos publicados:
  sensors/room/{room_id}/temperature  → {"value": float, "tick": int, "timestamp": str}
  sensors/room/{room_id}/humidity     → {"value": float, "tick": int, "timestamp": str}
  sensors/room/{room_id}/presence     → {"value": 0|1,   "tick": int, "timestamp": str}
  devices/ac/{device_id}/status       → {"power": "on"|"off", "setpoint": float}
  devices/ac/{device_id}/feedback     → {"power": "on"|"off", "setpoint": float}

Subscreve em:
  devices/ac/{device_id}/commands     → para receber comandos e simular feedback

Uso:
  python simulator.py
  MQTT_BROKER=localhost MQTT_PORT=1883 INTERVAL=5 python simulator.py
"""
from __future__ import annotations
import json
import logging
import math
import os
import random
import signal
import sys
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List

import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Configurações ────────────────────────────────────────────────────────────
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL = float(os.getenv("INTERVAL", "5"))        # segundos entre publicações
HAS_PRESENCE_ROOMS = {0, 1, 4, 5, 9, 10}           # índices com sensor de presença

# ── Definição das 14 salas ───────────────────────────────────────────────────
ROOMS = [
    # id (simples para tópicos), nome, andar, área, base_temp
    ("room-101", "Sala TI",         1, 45.0, 23.5),
    ("room-102", "Sala RH",         1, 30.0, 24.0),
    ("room-103", "Reuniões",        1, 25.0, 22.5),
    ("room-104", "Recepção",        1, 20.0, 25.0),
    ("room-201", "Diretoria",       2, 60.0, 22.0),
    ("room-202", "Financeiro",      2, 40.0, 23.0),
    ("room-203", "Jurídico",        2, 35.0, 23.5),
    ("room-204", "Marketing",       2, 40.0, 24.5),
    ("room-205", "Auditório",       2, 80.0, 21.5),
    ("room-301", "P&D",             3, 55.0, 22.0),
    ("room-302", "Laboratório",     3, 50.0, 23.0),
    ("room-303", "Suporte",         3, 30.0, 24.0),
    ("room-304", "Treinamento",     3, 45.0, 22.5),
    ("room-305", "Almoxarifado",    3, 25.0, 26.0),
]

AC_ROOMS = [r[0] for r in ROOMS]  # todos os quartos têm AC


class RoomSimulator:
    """Estado e lógica de simulação de uma sala."""

    def __init__(self, room_id: str, name: str, floor: int,
                 area_m2: float, base_temp: float, has_presence: bool) -> None:
        self.room_id = room_id
        self.name = name
        self.floor = floor
        self.area_m2 = area_m2
        self.base_temp = base_temp
        self.has_presence = has_presence

        # Estado mutable
        self.temperature = base_temp
        self.humidity = 55.0
        self.presence = 0
        self.ac_on = False
        self.setpoint = 24.0
        self._tick = 0

        # Padrões de ocupação: prob de presença por hora (0-23)
        self._occupancy_pattern = [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 0-5h
            0.1, 0.3, 0.8, 0.9, 0.9, 0.9,  # 6-11h
            0.7, 0.9, 0.9, 0.9, 0.8, 0.6,  # 12-17h
            0.4, 0.3, 0.1, 0.0, 0.0, 0.0,  # 18-23h
        ]

    def step(self, now: datetime) -> None:
        """Avança a simulação um passo."""
        self._tick += 1
        hour = now.hour
        minute = now.minute

        # Oscilação de temperatura ao longo do dia
        daily_variation = 3.0 * math.sin(math.pi * (hour - 6) / 12)
        noise = random.gauss(0, 0.15)

        # Efeito do AC
        if self.ac_on:
            ac_effect = -0.3 * (self.temperature - self.setpoint)
        else:
            ac_effect = 0.1  # aquece levemente sem AC

        self.temperature = round(
            self.base_temp + daily_variation + noise + ac_effect, 1
        )
        self.temperature = max(18.0, min(40.0, self.temperature))

        # Umidade: inversamente correlacionada com temperatura
        self.humidity = round(
            60.0 - (self.temperature - 22.0) * 1.5 + random.gauss(0, 1.5), 1
        )
        self.humidity = max(20.0, min(95.0, self.humidity))

        # Presença: probabilidade baseada no horário
        if self.has_presence:
            occ_prob = self._occupancy_pattern[hour]
            if random.random() < 0.05:  # 5% de chance de mudar estado
                self.presence = 1 if random.random() < occ_prob else 0
            # Liga AC automaticamente se há presença e temp fora do ideal
            if self.presence == 1 and not self.ac_on:
                if self.temperature > 25.5 or self.temperature < 21.0:
                    self.ac_on = True
                    logger.debug("%s: AC ligado automaticamente (presença + temp %.1f°C)",
                                 self.room_id, self.temperature)
        else:
            # Salas sem sensor de presença: AC ligado em horário comercial
            self.ac_on = 7 <= hour < 21

    def on_command(self, payload: dict) -> None:
        """Processa comando recebido via MQTT."""
        action = payload.get("action", "")
        if action == "on":
            self.ac_on = True
        elif action == "off":
            self.ac_on = False
        elif action == "setpoint":
            val = payload.get("value")
            if val is not None:
                self.setpoint = float(val)
        logger.info("%s: comando recebido action=%s value=%s",
                    self.room_id, action, payload.get("value"))


class SmartBuildingSimulator:
    """Orquestra todos os simuladores de sala + cliente MQTT."""

    def __init__(self) -> None:
        self.rooms: List[RoomSimulator] = []
        self.client = mqtt.Client(client_id="smartbuilding-simulator")
        self.running = False
        self._tick = 0
        self._setup_rooms()

    def _setup_rooms(self) -> None:
        for idx, (room_id, name, floor, area, base_temp) in enumerate(ROOMS):
            self.rooms.append(RoomSimulator(
                room_id=room_id, name=name, floor=floor,
                area_m2=area, base_temp=base_temp,
                has_presence=(idx in HAS_PRESENCE_ROOMS),
            ))

    def connect(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_command

        retries = 0
        while retries < 10:
            try:
                self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                self.client.loop_start()
                logger.info("Conectado ao broker %s:%d", MQTT_BROKER, MQTT_PORT)
                return
            except Exception as exc:
                retries += 1
                logger.warning("Tentativa %d/10 falhou: %s. Aguardando 3s...", retries, exc)
                time.sleep(3)

        raise ConnectionError(f"Não foi possível conectar ao broker {MQTT_BROKER}:{MQTT_PORT}")

    def _on_connect(self, client, userdata, flags, rc: int) -> None:
        if rc == 0:
            logger.info("MQTT conectado. Subscrevendo em tópicos de comando...")
            for room in self.rooms:
                topic = f"devices/ac/{room.room_id}/commands"
                client.subscribe(topic, qos=1)
        else:
            logger.error("Falha na conexão MQTT, rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc: int) -> None:
        if rc != 0:
            logger.warning("Desconexão inesperada rc=%d. Reconectando...", rc)

    def _on_command(self, client, userdata, message: mqtt.MQTTMessage) -> None:
        """Recebe comandos e repassa ao simulador da sala."""
        topic = message.topic
        try:
            payload = json.loads(message.payload.decode())
        except Exception:
            return
        # Topic: devices/ac/{room_id}/commands
        parts = topic.split("/")
        if len(parts) >= 3:
            room_id = parts[2]
            for room in self.rooms:
                if room.room_id == room_id:
                    room.on_command(payload)
                    # Publica feedback imediato
                    feedback = {
                        "power": "on" if room.ac_on else "off",
                        "setpoint": room.setpoint,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    fb_topic = f"devices/ac/{room_id}/feedback"
                    self.client.publish(fb_topic, json.dumps(feedback), qos=1)
                    break

    def _publish_all(self) -> None:
        """Publica leituras de todas as salas."""
        now = datetime.now(timezone.utc)
        self._tick += 1

        for room in self.rooms:
            room.step(now)
            ts = now.isoformat()

            # Temperatura
            self.client.publish(
                f"sensors/room/{room.room_id}/temperature",
                json.dumps({"value": room.temperature, "tick": self._tick,
                            "timestamp": ts, "sensor_id": f"temp-{room.room_id}"}),
                qos=0,
            )

            # Umidade
            self.client.publish(
                f"sensors/room/{room.room_id}/humidity",
                json.dumps({"value": room.humidity, "tick": self._tick,
                            "timestamp": ts, "sensor_id": f"umid-{room.room_id}"}),
                qos=0,
            )

            # Presença (apenas salas equipadas)
            if room.has_presence:
                self.client.publish(
                    f"sensors/room/{room.room_id}/presence",
                    json.dumps({"value": room.presence, "tick": self._tick,
                                "timestamp": ts, "sensor_id": f"pres-{room.room_id}"}),
                    qos=0,
                )

            # Status do AC
            self.client.publish(
                f"devices/ac/{room.room_id}/status",
                json.dumps({"power": "on" if room.ac_on else "off",
                            "setpoint": room.setpoint,
                            "temperature": room.temperature,
                            "timestamp": ts}),
                qos=0,
            )

        if self._tick % 12 == 0:  # log a cada ~1 min (12 * 5s)
            summary = " | ".join(
                f"{r.room_id}: {r.temperature}°C {r.humidity}% "
                f"{'🟢' if r.ac_on else '🔴'}"
                for r in self.rooms[:4]
            )
            logger.info("Tick %d | %s | ...", self._tick, summary)

    def run(self) -> None:
        self.running = True
        logger.info("Simulador iniciado — %d salas | intervalo: %ss", len(self.rooms), INTERVAL)
        logger.info("Broker: %s:%d", MQTT_BROKER, MQTT_PORT)

        try:
            while self.running:
                self._publish_all()
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Simulador encerrado. Total de ticks: %d", self._tick)


def main() -> None:
    sim = SmartBuildingSimulator()

    def handle_signal(sig, frame):
        logger.info("Sinal %d recebido. Encerrando...", sig)
        sim.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    sim.connect()
    time.sleep(2)  # aguarda conexão estabilizar
    sim.run()


if __name__ == "__main__":
    main()
