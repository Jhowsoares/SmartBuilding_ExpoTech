# Tópicos MQTT

Broker Mosquitto na porta **1883**. Payload em JSON.

## Sensores → Broker

```
sensors/room/{room_id}/temperature
sensors/room/{room_id}/humidity
sensors/room/{room_id}/presence
sensors/room/{room_id}/window
```

Payload padrão:

```json
{
  "value": 24.3,
  "timestamp": "2026-05-24T23:00:00Z",
  "tick": 42
}
```

- `value`: °C, %, 0|1 (presença/janela)
- `room_id`: ex. `room-101`, `room-esp32`, `room-eletrica`

## Backend → AC (comandos)

```
devices/ac/{device_id}/commands
```

```json
{"action": "on"}
{"action": "off"}
{"action": "setpoint", "value": 23.0}
```

## AC → Backend (feedback)

```
devices/ac/{device_id}/feedback
```

```json
{"power": "on", "setpoint": 23.0, "timestamp": "..."}
```

## Backend subscriptions

| Pattern | Handler |
|---------|---------|
| `sensors/room/+/temperature` | Persistência + regras |
| `sensors/room/+/humidity` | Persistência |
| `sensors/room/+/presence` | RN01 |
| `sensors/room/+/window` | RN02 |
| `devices/ac/+/feedback` | Estado em memória |

Simulador publica a cada **5 segundos** para 14 salas.
