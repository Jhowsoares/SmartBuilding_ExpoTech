/**
 * Smart Building — ESP32 gateway Bluetooth Classic (HC-05) → MQTT
 * Opção C: HC-05 permanece em D7/D8 no Arduino; ESP32 conecta sem fios.
 *
 * Placa: ESP32-WROOM com Bluetooth Classic (SPP).
 * Arduino: firmware arduino_ac_controller (9600 baud em D7/D8).
 *
 * Bibliotecas: PubSubClient, ArduinoJson v6+, BluetoothSerial (core ESP32)
 *
 * Arquitetura de tasks (correção do assert xEventGroupWaitBits):
 *   - Core 1 (loop): Wi-Fi + MQTT + leitura/publicação de telemetria.
 *   - Core 0 (bluetoothTask): inicialização única do rádio BT Classic e
 *     reconexão ao HC-05, isolada da pilha Wi-Fi/PubSubClient.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "BluetoothSerial.h"
#include "config.h"
#include "esp_wifi.h"
#include "esp_task_wdt.h"

#if DHT_ENABLED
#include "DHT.h"
DHT dht(DHT_GPIO, DHT_IS_DHT22 ? DHT22 : DHT11);
unsigned long lastDhtRead = 0;
#endif


#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Bluetooth Classic não habilitado. Use placa ESP32-WROOM e core ESP32 Arduino 2.x+"
#endif

BluetoothSerial SerialBT;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

char topicTemp[64];
char topicHum[64];
char topicCmd[64];
char topicPow[64];
char topicVolt[64];
char topicCurr[64];
char topicFb[64];   // devices/ac/<room>/feedback — estado real do AC

// Estado de energia do AC (ligado/desligado) confirmado pelo hardware
bool acPoweredOn = false;

String linkLine;
uint32_t tick = 0;
volatile bool streamConfigured = false;
unsigned long lastMqttAttempt = 0;   // throttle de reconexão MQTT no loop

// Handle da task dedicada do Bluetooth (Core 0)
TaskHandle_t btTaskHandle = NULL;

// Declarações antecipadas (usadas pela bluetoothTask)
bool connectBluetoothOnce();
void scanBluetooth();

struct Telemetry {
  bool ok = false;
  float temp = NAN;
  float hum = NAN;
  float vac = 0;
  float iac = 0;
  float pac = 0;
  int relay = 0;
};

Telemetry parseTelemetry(const String &line) {
  Telemetry t;
  // Formato REAL do Arduino (auto-stream): "V:31.85 I:0.16A P:5.25W"
  // Tokens separados por espaço; valores podem ter sufixo de unidade (A, W, V).
  // Também tolera TEMP/HUM caso o DHT11 volte a funcionar.
  if (line.indexOf("V:") < 0 && line.indexOf("P:") < 0 &&
      line.indexOf("TEMP:") < 0) {
    return t;  // não é linha de telemetria
  }

  int start = 0;
  while (start < (int)line.length()) {
    int sep = line.indexOf(' ', start);
    String token = (sep < 0) ? line.substring(start) : line.substring(start, sep);
    token.trim();
    int colon = token.indexOf(':');
    if (colon > 0) {
      String key = token.substring(0, colon);
      String val = token.substring(colon + 1);
      // Remove sufixos de unidade (0.16A → 0.16, 5.25W → 5.25)
      val.replace("A", "");
      val.replace("W", "");
      float f = val.toFloat();
      if (key == "V") t.vac = f;
      else if (key == "I") t.iac = f;
      else if (key == "P") t.pac = f;
      else if (key == "TEMP" || key == "T") t.temp = f;
      else if (key == "HUM" || key == "H") t.hum = f;
      else if (key == "REL") t.relay = val.toInt();
    }
    if (sep < 0) break;
    start = sep + 1;
  }
  // Linha válida se trouxe ao menos uma grandeza elétrica
  t.ok = (t.vac != 0.0f || t.iac != 0.0f || t.pac != 0.0f);
  return t;
}

void arduinoSend(const char *cmd) {
  if (!SerialBT.connected()) {
    Serial.printf("[BT] desconectado — não enviou: %s\n", cmd);
    return;
  }
  SerialBT.print(cmd);
  SerialBT.print('\n');
  Serial.printf("[BT→Arduino] %s\n", cmd);
}

void publishMqtt(const char *topic, float value, const char *sensorSuffix) {
  StaticJsonDocument<192> doc;
  doc["value"] = round(value * 100.0f) / 100.0f;   // 2 casas (preserva corrente baixa)
  doc["tick"] = tick;
  char sid[48];
  snprintf(sid, sizeof(sid), "%s-%s", sensorSuffix, ROOM_ID);
  doc["sensor_id"] = sid;

  char buf[192];
  serializeJson(doc, buf);
  if (mqtt.publish(topic, buf, false)) {
    Serial.printf("[MQTT] %s = %.1f\n", topic, value);
  } else {
    Serial.printf("[MQTT] falha %s\n", topic);
  }
}

void publishFeedback() {
  // Confirma para o backend/frontend o estado REAL aplicado no hardware.
  StaticJsonDocument<128> doc;
  doc["power"] = acPoweredOn ? "on" : "off";
  doc["source"] = "esp32-gateway";
  char buf[128];
  serializeJson(doc, buf);
  if (mqtt.publish(topicFb, buf, false)) {
    Serial.printf("[MQTT] feedback %s = %s\n", topicFb, acPoweredOn ? "on" : "off");
  }
}

void handleTelemetryLine(const String &line) {
  Telemetry t = parseTelemetry(line);

  if (t.ok) {
    // Calibração: converte o valor cru do ZMPT101B/ACS712 em grandeza realista
    float vCal = t.vac * VOLTAGE_CALIBRATION;
    float iCal = t.iac * CURRENT_CALIBRATION;
#if RECOMPUTE_POWER
    float pCal = vCal * iCal;                 // P = V·I (mais coerente)
#else
    float pCal = t.pac * VOLTAGE_CALIBRATION; // escala a P bruta do Arduino
#endif

    // Energia (sempre presente no stream real do Arduino)
    publishMqtt(topicPow, pCal, "pot");
    publishMqtt(topicVolt, vCal, "tensao");
    publishMqtt(topicCurr, iCal, "corrente");

    // Temperatura/umidade só quando o DHT11 estiver funcionando
    if (!isnan(t.temp) && t.temp >= 5.0f && t.temp <= 55.0f) {
      publishMqtt(topicTemp, t.temp, "temp");
    }
    if (!isnan(t.hum) && t.hum >= 5.0f && t.hum <= 100.0f) {
      publishMqtt(topicHum, t.hum, "umid");
    }

    Serial.printf("[ENERGIA] bruto(%.2fV %.2fA %.2fW) -> cal(%.1fV %.3fA %.1fW)\n",
                  t.vac, t.iac, t.pac, vCal, iCal, pCal);
    tick++;
    return;
  }

  // Demais linhas: mensagens informativas do Arduino (modos, erros, echo de cmd)
  Serial.printf("[Arduino] %s\n", line.c_str());
}

void onMqttMessage(char *topic, byte *payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  StaticJsonDocument<128> doc;
  if (deserializeJson(doc, msg) != DeserializationError::Ok) return;

  const char *action = doc["action"] | "";
  if (strcmp(action, "on") == 0) {
    arduinoSend("L");
    acPoweredOn = true;
    publishFeedback();
  } else if (strcmp(action, "off") == 0) {
    arduinoSend("D");
    acPoweredOn = false;
    publishFeedback();
  } else if (strcmp(action, "setpoint") == 0) {
    Serial.printf("[CMD] setpoint %.1f°C (IR no Arduino)\n", doc["value"] | 23.0f);
  } else if (strcmp(action, "auto") == 0) {
    arduinoSend("A");
  } else if (strcmp(action, "manual") == 0) {
    arduinoSend("M");
  }
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  delay(100);

  // Compatibilidade com hotspots 2.4 GHz (b/g/n)
  esp_wifi_set_protocol(WIFI_IF_STA, WIFI_PROTOCOL_11B | WIFI_PROTOCOL_11G | WIFI_PROTOCOL_11N);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Conectando ao Wi-Fi: %s", WIFI_SSID);

  // Loop de tentativa estendido para 25 segundos
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 25000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("IP ESP32: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi falhou — reiniciando");
    delay(1000);
    ESP.restart();
  }
}


// Tentativa ÚNICA e não-bloqueante de conectar ao MQTT.
// Retorna true se conectou. A telemetria via BT continua mesmo sem broker.
bool connectMqtt() {
  if (mqtt.connected()) return true;

  char clientId[32];
  snprintf(clientId, sizeof(clientId), "esp32-bt-%s", ROOM_ID);
  Serial.printf("[MQTT] conectando ao broker (%s:%d)... ", MQTT_BROKER, MQTT_PORT);

  if (mqtt.connect(clientId)) {
    mqtt.subscribe(topicCmd);
    Serial.printf("OK — sub %s\n", topicCmd);
    return true;
  }
  Serial.printf("falhou, erro %d (tenta de novo em breve)\n", mqtt.state());
  return false;
}

void scanBluetooth() {
  Serial.println("[BT] Scan 10s — anote o nome/MAC do HC-05:");

  // Na versão 3.x, o discover inicia o scan e retorna um booleano de sucesso
  if (!SerialBT.discover(10000)) {
    Serial.println("[BT] Scan falhou");
    return;
  }

  // Em seguida, pegamos os resultados acumulados na memória
  BTScanResults* results = SerialBT.getScanResults();
  if (!results) {
    Serial.println("[BT] Nenhum resultado obtido");
    return;
  }

  int count = results->getCount();
  for (int i = 0; i < count; i++) {
    // Usamos um ponteiro (*) para corrigir o erro de classe abstrata
    BTAdvertisedDevice* device = results->getDevice(i);
    if (device != nullptr) {
      // Imprime o MAC para você copiar em HC05_MAC (config.h) — conexão por MAC
      // é bem mais robusta que por nome.
      Serial.printf("  %2d | MAC %s | %s | RSSI %d\n",
                    i + 1,
                    device->getAddress().toString().c_str(),
                    device->haveName() ? device->getName().c_str() : "(sem nome)",
                    device->getRSSI());

      if (device->haveCOD()) {
        Serial.printf("      COD: 0x%06X\n", device->getCOD());
      }
    }
  }
  Serial.printf("[BT] %d dispositivos encontrados\n", count);
}

// ── Tentativa ÚNICA de conexão (chamada SOMENTE pela bluetoothTask) ──────────
// Não chama SerialBT.begin()/end() aqui: o rádio é inicializado uma única vez
// no início da task. Aqui apenas tentamos o connect() e configuramos o stream.
bool connectBluetoothOnce() {
  Serial.printf("[BT] Conectando a '%s' (timeout %lu ms)...\n", HC05_DEVICE_NAME, BT_CONNECT_TIMEOUT);

  bool ok = false;
#if USE_HC05_MAC
  ok = SerialBT.connect(HC05_MAC);          // conexão por MAC (mais robusta/rápida)
#else
  ok = SerialBT.connect(HC05_DEVICE_NAME);  // conexão por nome
#endif

  if (!ok) {
    Serial.println("[BT] connect() retornou false");
    return false;
  }

  unsigned long start = millis();
  while (!SerialBT.connected() && (millis() - start) < BT_CONNECT_TIMEOUT) {
    vTaskDelay(pdMS_TO_TICKS(200));
  }

  if (!SerialBT.connected()) {
    Serial.println("[BT] Timeout aguardando conexão SPP");
    SerialBT.disconnect();
    return false;
  }

  Serial.println("[BT] Conectado ao HC-05");
  vTaskDelay(pdMS_TO_TICKS(300));

  // NÃO enviar "STREAM:N" nem "T": o firmware real do Arduino lê caractere a
  // caractere, então "STREAM:5" vira os comandos S,T,R,E,A,M — disparando os
  // modos AUTOMATICO/MANUAL sem querer. O Arduino já transmite V/I/P sozinho;
  // aqui apenas ouvimos.
  streamConfigured = true;
  return true;
}

// ── Task dedicada do Bluetooth (Core 0) ──────────────────────────────────────
// Isola TODA a inicialização e reconexão do rádio BT Classic da pilha
// Wi-Fi/MQTT (Core 1). Isso elimina a corrida de recursos no FreeRTOS que
// disparava "assert failed: xEventGroupWaitBits" ao chamar begin()/connect()
// dentro do loop() principal.
void bluetoothTask(void *pvParameters) {
  Serial.printf("[BT-Task] iniciada no core %d\n", xPortGetCoreID());

  // Inicializa o rádio BT Classic UMA única vez, já fora do contexto do loop().
  if (!SerialBT.begin("ESP32-SB-Gateway", true)) {
    Serial.println("[BT-Task] Falha ao iniciar BluetoothSerial — encerrando task");
    btTaskHandle = NULL;
    vTaskDelete(NULL);
    return;
  }
  Serial.println("[BT-Task] BluetoothSerial (master) pronto");

  // CRÍTICO p/ HC-05: o módulo usa pareamento LEGADO com PIN fixo.
  // No core 3.x, esp_bt_gap_set_pin() precisa do stack JÁ iniciado, então
  // setPin() tem que vir DEPOIS de begin() para realmente aplicar o PIN.
  if (!SerialBT.setPin(HC05_PIN, strlen(HC05_PIN))) {
    Serial.println("[BT-Task] Aviso: setPin() falhou (segue mesmo assim)");
  } else {
    Serial.printf("[BT-Task] PIN legado configurado: %s\n", HC05_PIN);
  }

  // Scan inicial de diagnóstico: revela NOME e MAC reais do módulo.
  // Se o seu HC-05 não se chama exatamente "HC-05", é por isso que o
  // connect() por nome falha. Anote o MAC e use USE_HC05_MAC em config.h.
  Serial.println("[BT-Task] Scan inicial para identificar o módulo:");
  scanBluetooth();

  uint8_t failures = 0;

  for (;;) {
    if (!SerialBT.connected()) {
      streamConfigured = false;

      if (connectBluetoothOnce()) {
        failures = 0;
      } else {
        failures++;
        // A cada 5 falhas seguidas, roda um scan de diagnóstico
        if (failures % 5 == 0) {
          Serial.println("[BT-Task] Várias falhas seguidas — scan de diagnóstico:");
          scanBluetooth();
          Serial.println("[BT-Task] Ajuste HC05_DEVICE_NAME ou USE_HC05_MAC em config.h");
        }
      }
    }

    // Libera o Core 0 e dá ritmo às tentativas de reconexão (proteção de tempo)
    vTaskDelay(pdMS_TO_TICKS(5000));
  }
}

#if DHT_ENABLED
// Lê o DHT11 ligado ao ESP32 e publica temperatura/umidade (não-bloqueante).
void readDHT() {
  if (millis() - lastDhtRead < DHT_INTERVAL_MS) return;
  lastDhtRead = millis();

  float h = dht.readHumidity();
  float t = dht.readTemperature();  // °C

  if (isnan(h) || isnan(t)) {
    Serial.println("[DHT] leitura falhou (NaN) — confira S/3V3/GND e o GPIO");
    return;
  }

  if (t >= 5.0f && t <= 55.0f) publishMqtt(topicTemp, t, "temp");
  if (h >= 5.0f && h <= 100.0f) publishMqtt(topicHum, h, "umid");
  Serial.printf("[DHT] Temp=%.1f C  Umid=%.1f %%\n", t, h);
}
#endif

void readBluetooth() {
  while (SerialBT.available()) {
    char c = (char)SerialBT.read();
    if (c == '\n' || c == '\r') {
      if (linkLine.length() > 0) {
        handleTelemetryLine(linkLine);
        linkLine = "";
      }
    } else if (linkLine.length() < 128) {
      linkLine += c;
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== ESP32 Gateway BT (Opção C) ===");
  Serial.println("Placa: ESP32-WROOM + HC-05 no Arduino D7/D8");

  snprintf(topicTemp, sizeof(topicTemp), "sensors/room/%s/temperature", ROOM_ID);
  snprintf(topicHum, sizeof(topicHum), "sensors/room/%s/humidity", ROOM_ID);
  snprintf(topicCmd, sizeof(topicCmd), "devices/ac/%s/commands", ROOM_ID);
  snprintf(topicPow, sizeof(topicPow), "sensors/room/%s/power", ROOM_ID);
  snprintf(topicVolt, sizeof(topicVolt), "sensors/room/%s/voltage", ROOM_ID);
  snprintf(topicCurr, sizeof(topicCurr), "sensors/room/%s/current", ROOM_ID);
  snprintf(topicFb, sizeof(topicFb), "devices/ac/%s/feedback", ROOM_ID);

  Serial.printf("Room ID : %s\n", ROOM_ID);
  Serial.printf("HC-05   : %s\n", HC05_DEVICE_NAME);
  Serial.printf("Temp    : %s\n", topicTemp);
  Serial.printf("Cmd     : %s\n", topicCmd);

#if DHT_ENABLED
  dht.begin();
  Serial.printf("DHT11   : GPIO %d (clima da sala lido no ESP32)\n", DHT_GPIO);
#endif

  connectWiFi();
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);

  // Dá tempo para os sockets do Wi-Fi estabilizarem antes do 1º connect MQTT
  delay(1500);
  connectMqtt();

  Serial.println("Gateway de rede pronto. Iniciando task de Bluetooth no Core 0...");

  // Cria a task dedicada do BT no Core 0 — Wi-Fi/MQTT permanecem no Core 1.
  xTaskCreatePinnedToCore(
    bluetoothTask,   // função da task
    "BT_Task",       // nome
    4096,            // tamanho da stack (words)
    NULL,            // parâmetro
    1,               // prioridade baixa
    &btTaskHandle,   // handle
    0                // Core 0
  );

#if WDT_TIMEOUT_S > 0
  // Watchdog: reinicia o ESP32 se o loop() travar por mais que WDT_TIMEOUT_S.
  esp_task_wdt_config_t wdtCfg = {
    .timeout_ms = (uint32_t)(WDT_TIMEOUT_S * 1000),
    .idle_core_mask = 0,
    .trigger_panic = true,
  };
  // Se o core já tiver inicializado o WDT, apenas reconfigura.
  if (esp_task_wdt_init(&wdtCfg) == ESP_ERR_INVALID_STATE) {
    esp_task_wdt_reconfigure(&wdtCfg);
  }
  esp_task_wdt_add(NULL);   // monitora a task do loop()
  Serial.printf("[WDT] watchdog de %d s ativo\n", WDT_TIMEOUT_S);
#endif
}

void loop() {
  // ── Core 1: somente rede (Wi-Fi/MQTT) e leitura/publicação de telemetria. ──
  // A conexão/reconexão do Bluetooth roda na bluetoothTask (Core 0).

  // Se o Wi-Fi cair por qualquer oscilação de energia da tomada, reconecta
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Reconexão MQTT não-bloqueante: tenta no máximo a cada 3 s, sem travar o
  // loop. Assim a telemetria via BT continua mesmo com o broker oscilando.
  if (!mqtt.connected() && (millis() - lastMqttAttempt > 3000)) {
    lastMqttAttempt = millis();
    connectMqtt();
  }
  mqtt.loop();

  // Lê as linhas recebidas do Arduino via BT e publica no MQTT (sem bloquear).
  readBluetooth();

#if DHT_ENABLED
  // Lê o DHT11 do ESP32 e publica temperatura/umidade da sala.
  readDHT();
#endif

#if WDT_TIMEOUT_S > 0
  esp_task_wdt_reset();   // alimenta o watchdog — o loop está vivo
#endif

  delay(10);  // cede o processador, evitando sobrecarga
}
