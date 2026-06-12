/**
 * ESP32 ↔ Arduino via HC-05 (Bluetooth Classic SPP) — Opção C
 *
 * Placa: ESP32-WROOM (DevKit v1, NodeMCU-32S). NÃO use ESP32-C3 (sem BT Classic).
 */
#pragma once

// ── Wi-Fi ────────────────────────────────────────────────────────────────────
#define WIFI_SSID     "esp_note"
#define WIFI_PASSWORD "bism6132"

// ── MQTT (IP do notebook — ipconfig na Wi-Fi) ────────────────────────────────
#define MQTT_BROKER   "192.168.137.1"
#define MQTT_PORT     1883

// Sala alinhada ao simulador (Laboratório = room-302)
#define ROOM_ID       "room-302"

// ── HC-05 (modo SLAVE, 9600 baud) ───────────────────────────────────────────
// Use o NOME configurado no módulo (AT+NAME). Padrão de fábrica: "HC-05"
#define HC05_DEVICE_NAME  "HC-05"

// Opcional: se souber o MAC (ex.: {0x98,0xD3,0x31,0xF5,0xAA,0xBB}), defina USE_HC05_MAC 1
// Conectar por MAC é mais rápido/robusto (evita a fase de discovery).
#define USE_HC05_MAC      0
#if USE_HC05_MAC
static const uint8_t HC05_MAC[6] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
#endif

// PIN do HC-05 (só necessário no primeiro pareamento em alguns módulos)
#define HC05_PIN          "1234"

// ── Telemetria / link ────────────────────────────────────────────────────────
#define ARDUINO_BAUD         9600
#define ARDUINO_STREAM_SEC   5       // STREAM:N enviado ao Arduino após conectar BT
#define POLL_INTERVAL_MS     5000UL // se STREAM:0, pede T a cada N ms
#define BT_RECONNECT_MS      8000UL // tenta reconectar ao HC-05
#define BT_CONNECT_TIMEOUT   15000UL

// ── Calibração de energia ────────────────────────────────────────────────────
// O Arduino envia o valor CRU do ZMPT101B/ACS712 (ex.: "V:31.85"), que NÃO é a
// tensão real da rede. Para mostrar valores realistas no dashboard, medimos a
// tensão real com um multímetro e calculamos o fator:
//     VOLTAGE_CALIBRATION = tensao_real_medida / valor_bruto_exibido
// Ex.: rede 127 V e bruto ~34 → 127/33.96 ≈ 3.74. Ajuste ao seu caso!
// Deixe 1.0 para publicar o valor bruto (sem calibrar).
#define VOLTAGE_CALIBRATION   3.74f   // 127 V / bruto médio ~33.96
#define CURRENT_CALIBRATION   1.0f    // ACS712: ajuste se a corrente também estiver crua
// Potência recalculada como V_cal * I_cal (mais coerente que escalar P bruto).
#define RECOMPUTE_POWER       1       // 1 = P = Vcal*Ical ; 0 = usa P do Arduino

// ── Watchdog ──────────────────────────────────────────────────────────────────
// Reinicia o ESP32 se o loop principal travar por mais que este tempo (s).
#define WDT_TIMEOUT_S         30

// ── DHT11 no ESP32 (clima da sala) ──────────────────────────────────────────
// Sensor DHT11 ligado DIRETO a um GPIO do ESP32 (Opção B/A). O Arduino não
// transmite clima pelo BT, então lemos aqui e publicamos em .../temperature
// e .../humidity. Requer as libs (Arduino IDE → Library Manager):
//   "DHT sensor library" (Adafruit) + "Adafruit Unified Sensor".
// Ligação (módulo azul de 3 pinos): S → DHT_GPIO | + → 3V3 | − → GND.
#define DHT_ENABLED      1        // 0 = desativa (e dispensa as libs)
#define DHT_GPIO         4        // GPIO de dados do DHT11
#define DHT_IS_DHT22     0        // 1 se for DHT22 (azul maior); 0 = DHT11
#define DHT_INTERVAL_MS  2500UL   // DHT11 não aceita leituras < 2 s
