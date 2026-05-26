# Guia de Hardware — ESP32

> Para rodar só o simulador, pule para [Setup](./setup.md).

## Componentes (1 nó de teste)

| Componente | Função |
|------------|--------|
| ESP32 DevKit v1 | Microcontrolador Wi-Fi + MQTT |
| BME280 (I2C, 3.3V) | Temperatura + Umidade |
| HC-SR501 (PIR, 5V) | Presença |
| LED IR 940nm + 330Ω | Simula comando AC |
| Protoboard + jumpers | Montagem |

## Pinagem

```
ESP32 DevKit v1
  3V3  ─── VCC (BME280)
  GND  ─── GND (BME280, HC-SR501, cátodo LED)
  GPIO 21 (SDA) ─── BME280 SDA
  GPIO 22 (SCL) ─── BME280 SCL
  5V   ─── VCC (HC-SR501)
  GPIO 13 ─── OUT (HC-SR501)
  GPIO 4 ── 330Ω ─── Anodo LED IR
```

Firmware pronto: [`firmware/esp32_smartbuilding/esp32_smartbuilding.ino`](../firmware/esp32_smartbuilding/esp32_smartbuilding.ino)

## Tópicos MQTT

```cpp
client.publish("sensors/room/room-101/temperature",
  "{\"value\": 24.3, \"timestamp\": \"2026-05-24T23:00:00Z\"}");
client.publish("sensors/room/room-101/humidity", ...);
client.publish("sensors/room/room-101/presence", "{\"value\": 1, ...}");
client.subscribe("devices/ac/{device_uuid}/commands");
```

## Validar IR sem ar-condicionado

1. Abra a **câmera frontal** do celular.
2. Aponte o LED IR para a câmera.
3. No dashboard, desligue o AC da sala.
4. O LED pisca em **roxo/lilás** na tela — cadeia completa OK.

## Teste com TV doméstica

Codifique POWER OFF da TV com `IRremoteESP8266`. Quando RN01 disparar por ausência, a TV apaga — comportamento idêntico ao AC real.

## Ponte Arduino + Bluetooth (equipe elétrica)

Script: [`tools/bt_bridge.py`](../tools/bt_bridge.py)

```bash
pip install pyserial paho-mqtt
python tools/bt_bridge.py --port COM5 --room room-eletrica
```

O Arduino envia `Serial.println(temperatura)` via HC-05/HC-06.
