# Engenharia Elétrica

A Engenharia Elétrica conecta o **mundo físico** ao sistema digital: sensores, microcontroladores, comunicação sem fio e automação do ar-condicionado.

---

## Contexto no projeto

No laboratório de elétrica (subsolo), a equipe monta a **camada de hardware** que alimenta a plataforma Smart Building:

- Leitura de temperatura (e, quando disponível, presença)
- Transmissão dos dados até o backend
- Base física para controle do AC (via simulação ou IR)

> **Status da documentação:** o entregável formal em PDF/Word da equipe de Elétrica ainda **não foi adicionado** à pasta `entregaveis/`. Este documento consolida o que está implementado no repositório e no cronograma integrado.

---

## Arquitetura elétrica (visão simplificada)

```
Sensor (DHT/NTC) → Arduino Uno → Bluetooth HC-05 → Notebook (bt_bridge.py)
                                                          ↓
                                                    MQTT Mosquitto
                                                          ↓
                                                    Backend FastAPI
```

**Alternativa (ESP32):** sensores BME280 + PIR publicam direto via Wi-Fi/MQTT — ver [hardware ESP32](../sistema/hardware-esp32.md).

---

## Contribuições previstas (cronograma)

| # | Atividade |
|---|-----------|
| 1 | Montagem dos componentes no protoboard / preparação para maquete |
| 2 | Programação e testes iniciais do Arduino |
| 3 | Alinhamento da maquete com Civil (escala, materiais) |
| 4 | Entrega do Arduino montado para integração com o dashboard |
| 5 | Ajustes finais na maquete em conjunto com Civil |

---

## Componentes típicos

| Componente | Função |
|------------|--------|
| Sensor de temperatura | Mede ambiente para regras RN01–RN03 |
| Arduino Uno | Processa leituras e envia via serial/Bluetooth |
| Módulo Bluetooth HC-05 | Comunicação sem fio com o PC |
| Eletrodutos aparentes | Organização e proteção dos cabos (conceito visual) |
| ESP32 (opcional) | Publicação MQTT nativa + controle IR do AC |

---

## Integração com Computação

| Artefato no repositório | Descrição |
|-------------------------|-----------|
| [`tools/bt_bridge.py`](../../tools/bt_bridge.py) | Ponte Bluetooth → MQTT (formato `TEMP:24.5`) |
| [`firmware/esp32_smartbuilding/`](../../firmware/esp32_smartbuilding/) | Firmware alternativo com Wi-Fi/MQTT |
| Tópicos MQTT | `sensors/room/{id}/temperature` — ver [mqtt.md](../sistema/mqtt.md) |

**Formato serial esperado (Arduino):**
```
TEMP:24.5
PRES:1
HUM:65.2
```

---

## Integração com Civil e Produção

- **Civil:** maquete com passagens para cabos e sensores
- **Produção:** custo de sensores, Bluetooth e eletrodutos entram no CAPEX
- **Computação:** consome telemetria e envia comandos de controle

---

## Próximos passos (equipe Elétrica)

- [ ] Publicar entregável formal em `entregaveis/`
- [ ] Documentar esquema elétrico (pinagem, alimentação)
- [ ] Validar leituras calibradas contra termômetro de referência

---

## Documentos relacionados

- [Hardware ESP32](../sistema/hardware-esp32.md)
- [Conceito visual do laboratório (original)](entregaveis/visao-geral-laboratorio-original.md)
