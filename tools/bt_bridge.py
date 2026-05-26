#!/usr/bin/env python3
"""
bt_bridge.py — Ponte Bluetooth Serial → MQTT
Smart Building ExpoTech 2026

Conecta ao módulo Bluetooth do Arduino (HC-05 / HC-06) via porta COM,
lê a temperatura e publica no broker MQTT local, fazendo o sensor da
equipe de elétrica aparecer no dashboard como uma sala real.

Fluxo:
  Arduino → HC-05 Bluetooth → Notebook (porta COM) → este script → MQTT :1883

Dependências:
  pip install pyserial paho-mqtt

Como descobrir a porta COM do Bluetooth:
  Windows: Gerenciador de Dispositivos → Portas (COM e LPT)
           Procure "HC-05" ou "Porta COM Bluetooth"
  Linux/Mac: ls /dev/rfcomm* ou ls /dev/tty.HC*

O Arduino precisa enviar via Bluetooth Serial:
  Serial.println(temperatura);        → apenas o número float, ex: "23.5"
  Serial.println("T:" + temp_str);    → ou com prefixo T:

Uso:
  python bt_bridge.py
  python bt_bridge.py --port COM8 --room room-eletrica --broker 192.168.1.100
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone

try:
    import serial
except ImportError:
    print("ERRO: pyserial não instalado. Execute: pip install pyserial")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERRO: paho-mqtt não instalado. Execute: pip install paho-mqtt")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bt_bridge")


def parse_temperature(raw: str) -> float | None:
    """
    Aceita vários formatos enviados pelo Arduino:
      "23.5"
      "T:23.5"
      "TEMP=23.50"
      "Temperatura: 23.5 C"
    Retorna None se não conseguir extrair.
    """
    raw = raw.strip()
    if not raw:
        return None

    # Remove prefixos comuns
    for prefix in ("T:", "TEMP=", "Temperatura:", "temp:", "temperature:"):
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix):].strip()
            break

    # Remove unidade se houver (" C", "°C", "C")
    raw = raw.rstrip("°Cc ").strip()

    try:
        value = float(raw)
        if 5.0 <= value <= 55.0:  # RN08: faixa válida do sistema
            return round(value, 1)
        else:
            log.warning("Temperatura fora da faixa válida (5–55°C): %.1f — descartado", value)
            return None
    except ValueError:
        return None


def build_payload(value: float, tick: int, room_id: str) -> str:
    return json.dumps({
        "value": value,
        "tick": tick,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor_id": f"temp-{room_id}",
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ponte Bluetooth Serial → MQTT (Smart Building ExpoTech 2026)"
    )
    parser.add_argument("--port",    default="COM5",          help="Porta COM do Bluetooth (ex: COM5, /dev/rfcomm0)")
    parser.add_argument("--baud",    default=9600,  type=int, help="Baud rate do módulo BT (padrão: 9600)")
    parser.add_argument("--broker",  default="localhost",      help="Host do broker MQTT (padrão: localhost)")
    parser.add_argument("--mqport",  default=1883,  type=int, help="Porta do broker MQTT (padrão: 1883)")
    parser.add_argument("--room",    default="room-eletrica",  help="ID da sala no sistema (ex: room-eletrica)")
    parser.add_argument("--interval",default=5.0, type=float, help="Intervalo de publicação em segundos (padrão: 5)")
    args = parser.parse_args()

    topic_temp = f"sensors/room/{args.room}/temperature"

    log.info("=== Smart Building — Ponte Bluetooth → MQTT ===")
    log.info("Porta serial : %s @ %d baud", args.port, args.baud)
    log.info("Broker MQTT  : %s:%d", args.broker, args.mqport)
    log.info("Sala (room)  : %s", args.room)
    log.info("Tópico       : %s", topic_temp)
    log.info("Intervalo    : %.1fs", args.interval)

    # ── Conexão serial ──────────────────────────────────────────────────────
    try:
        ser = serial.Serial(args.port, args.baud, timeout=3)
        log.info("Porta %s aberta com sucesso", args.port)
    except serial.SerialException as exc:
        log.error("Não foi possível abrir %s: %s", args.port, exc)
        log.error("Dica: verifique o Gerenciador de Dispositivos e use --port COM<N>")
        sys.exit(1)

    # ── Conexão MQTT ────────────────────────────────────────────────────────
    client = mqtt.Client(client_id=f"bt-bridge-{args.room}")

    def on_connect(c, _userdata, _flags, rc):
        if rc == 0:
            log.info("MQTT conectado em %s:%d", args.broker, args.mqport)
        else:
            log.error("MQTT falhou com código %d", rc)

    def on_disconnect(c, _userdata, rc):
        if rc != 0:
            log.warning("MQTT desconectado inesperadamente (rc=%d) — reconectando...", rc)

    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(args.broker, args.mqport, keepalive=60)
    except Exception as exc:
        log.error("Não foi possível conectar ao MQTT %s:%d — %s", args.broker, args.mqport, exc)
        ser.close()
        sys.exit(1)

    client.loop_start()

    # ── Loop principal ──────────────────────────────────────────────────────
    log.info("Aguardando dados do Arduino via Bluetooth... (Ctrl+C para parar)")
    tick = 0
    last_publish = 0.0
    last_value: float | None = None

    try:
        while True:
            # Lê linha do serial Bluetooth
            try:
                raw_bytes = ser.readline()
                raw = raw_bytes.decode("utf-8", errors="replace").strip()
            except serial.SerialTimeoutException:
                raw = ""

            if raw:
                log.debug("Serial recebido: %r", raw)
                value = parse_temperature(raw)
                if value is not None:
                    last_value = value

            # Publica no intervalo configurado
            now = time.time()
            if last_value is not None and (now - last_publish) >= args.interval:
                if client.is_connected():
                    payload = build_payload(last_value, tick, args.room)
                    result = client.publish(topic_temp, payload, qos=1)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        log.info("Publicado | sala=%s temp=%.1f°C tick=%d", args.room, last_value, tick)
                    else:
                        log.warning("Falha ao publicar (rc=%d)", result.rc)
                    tick += 1
                    last_publish = now
                else:
                    log.warning("MQTT desconectado — pulando publicação")

            time.sleep(0.1)

    except KeyboardInterrupt:
        log.info("Encerrado pelo usuário")
    finally:
        client.loop_stop()
        client.disconnect()
        ser.close()
        log.info("Conexões encerradas")


if __name__ == "__main__":
    main()
