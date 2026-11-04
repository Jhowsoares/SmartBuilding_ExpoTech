# 🔌 Guia de Hardware e Firmware — ESP32 & Sensores

Este documento especifica a montagem de bancada, o mapeamento de pinagem (GPIOs) e a integração do nó de borda IoT baseado em **ESP32** para o ecossistema **Smart Building**.

> **Nota:** Para testar a aplicação sem hardware físico, utilize o [Guia de Setup e Execução do Simulador](../guias/setup.md).

---

## 🛠️ Especificação de Componentes (Nó de Teste)

| Componente | Especificação | Função no Sistema |
| :--- | :--- | :--- |
| **ESP32 DevKit v1** | Microcontrolador Dual-Core (Wi-Fi + BLE) | Processamento local, leitura de sensores e publicação MQTT |
| **BME280** | I2C, Alimentação 3.3V | Captação de Temperatura e Umidade Relativa |
| **HC-SR501** | Sensor PIR, Alimentação 5V | Detecção de presença humana (Gatilho para RN01) |
| **LED IR (940nm)** | Associado a resistor de 330Ω | Simulação de infravermelho para atuação em HVAC |

---

## 📐 Mapeamento de Pinagem (GPIO Pinout)

Conexões físicas realizadas na protoboard:

```text
ESP32 DevKit v1
  ├── 3.3V  ─────── VCC (BME280)
  ├── GND   ─────── GND (BME280, HC-SR501, Cátodo LED IR)
  ├── GPIO 21 ───── SDA (BME280 - Barramento I2C)
  ├── GPIO 22 ───── SCL (SCL BME280 - Barramento I2C)
  ├── 5V    ─────── VCC (HC-SR501)
  ├── GPIO 13 ───── OUT (HC-SR501 - Sinal de Presença)
  └── GPIO 4  ──[330Ω]── Ânodo LED IR (Atuação de Comando)

```

* **Código-fonte do Firmware:** O sketch completo em C++ para a IDE Arduino está versionado em `firmware/esp32_smartbuilding/esp32_smartbuilding.ino`.

---

## 📡 Tópicos MQTT Publicados e Subscritos

O microcontrolador gerencia os eventos de telemetria e o canal de comandos:

### Publicação de Telemetria (Pub)

* `sensors/room/room-101/temperature`
* `sensors/room/room-101/humidity`
* `sensors/room/room-101/presence`

### Escuta de Comandos (Sub)

* `devices/ac/{device_uuid}/commands`

---

## 🧪 Validação de Funcionamento Óptico (In-Lab Testing)

Para validar o disparo de comandos de atuação por infravermelho sem a necessidade de um equipamento de ar-condicionado real:

1. Abra a **câmera de um smartphone** (sensores de câmera possuem alta sensibilidade à luz infravermelha).
2. Aponte a câmera diretamente para o **LED IR (940nm)** montado na protoboard.
3. No painel de controle (Dashboard), dispare um comando de desligamento (`Power Off`) para a sala correspondente.
4. O LED IR emitirá flashes de luz visíveis pela lente da câmera (tonalidade roxa/lilás), confirmando o encadeamento completo do ciclo: *Regra de Negócio $\rightarrow$ MQTT $\rightarrow$ Microcontrolador $\rightarrow$ Atuador*.

---

## 🔗 Integração com Equipamentos via Bluetooth Bridge (Opcional)

Para cenários onde sensores legados utilizam conexão Serial/Bluetooth (como módulos HC-05/HC-06):

* **Script de Ponte:** `tools/bt_bridge.py`
* **Comando de Execução:**
```bash
pip install pyserial paho-mqtt
python tools/bt_bridge.py --port COM5 --room room-eletrica

```