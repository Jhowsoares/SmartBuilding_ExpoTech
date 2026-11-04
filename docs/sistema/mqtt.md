# 📡 Arquitetura de Mensageria e Tópicos MQTT

> **Broker:** Eclipse Mosquitto  
> **Porta Padrão:** `1883` (TCP) / `9001` (WebSockets)  
> **Formato dos Payloads:** JSON (UTF-8)

O protocolo MQTT é utilizado para a comunicação assíncrona de baixa latência entre os nós sensores (microcontroladores ESP32 e simuladores), o broker de mensageria e o backend FastAPI.

---

## 📥 1. Sensores → Broker (Ingestão de Telemetria)

Os nós de borda publicam leituras em tópicos estruturados por sala e tipo de grandeza.

### Tópicos Pub/Sub

* `sensors/room/{room_id}/temperature`
* `sensors/room/{room_id}/humidity`
* `sensors/room/{room_id}/presence`
* `sensors/room/{room_id}/window`

### Schema do Payload Padrão (JSON)
```json
{
  "value": 24.3,
  "timestamp": "2026-05-24T23:00:00Z",
  "tick": 42
}

```

### Dicionário de Campos e Unidades

| Parâmetro | Tipo | Unidade / Valores | Descrição |
| --- | --- | --- | --- |
| `value` | `float` / `int` | `°C` (temperatura), `%` (umidade), `0` ou `1` (presença/janela) | Valor medido pelo sensor no instante da leitura. |
| `timestamp` | `string` | ISO 8601 UTC | Carimbo de data/hora da captação na borda. |
| `tick` | `integer` | Contador sequencial | Identificador de sequência do pacote para detecção de perdas. |
| `room_id` | `string` | Ex: `room-101`, `room-esp32` | Identificador único da sala associada no banco. |

---

## 📤 2. Backend → Atuadores (Comandos HVAC)

Endpoints da API ou o motor de regras geram comandos de atuação publicados nos tópicos dos dispositivos de Ar-Condicionado (AC).

* **Tópico de Comando:** `devices/ac/{device_id}/commands`

### Exemplo de Comandos

* **Ligar Climatização:**
```json
{ "action": "on" }

```


* **Desligar Climatização:**
```json
{ "action": "off" }

```


* **Ajustar Setpoint de Temperatura:**
```json
{ "action": "setpoint", "value": 23.0 }

```



---

## 🔄 3. Atuadores → Backend (Feedback de Estado)

Dispositivos confirmam a execução do comando ou reportam mudança de estado físico.

* **Tópico de Confirmamento:** `devices/ac/{device_id}/feedback`

### Payload de Retroalimentação

```json
{
  "power": "on",
  "setpoint": 23.0,
  "timestamp": "2026-05-24T23:00:05Z"
}

```

---

## 🎧 4. Inscrições do Backend (Subscriptions & Wildcards)

O serviço de escuta no backend (`MQTT Handler`) utiliza *wildcards* para processar múltiplos nós em paralelo:

| Padrão do Tópico (Pattern) | Handler / Processador Assíncrono | Regra Associada |
| --- | --- | --- |
| `sensors/room/+/temperature` | Persistência em banco + cálculo de média móvel | Monitoramento Térmico |
| `sensors/room/+/humidity` | Persistência direta na tabela de telemetria | Conforto Ambiental |
| `sensors/room/+/presence` | Processamento do motor de regras | **RN01** (Desligamento por Ausência) |
| `sensors/room/+/window` | Processamento de bloqueio imediato | **RN02** (Trava com Janela Aberta) |
| `devices/ac/+/feedback` | Sincronização do estado em memória / Redis | Auditoria de Atuação |

---

## ⚡ Carga do Simulador de Telemetria

Para testes de estresse e validação do dashboard:

* O container `simulator` gera telemetria sintética publicando a cada **5 segundos** para **14 salas simultâneas**.
* QoS configurado: `QoS 0` (At most once) para telemetria de sensores e `QoS 1` (At least once) para comandos de atuação.

