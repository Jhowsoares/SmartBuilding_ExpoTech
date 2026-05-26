/**
 * Smart Building — Firmware ESP32
 * ExpoTech 2026
 *
 * Sensores suportados:
 *   - BME280 (I2C)  → temperatura + umidade
 *   - HC-SR501 (PIR) → presença
 *   - LED IR 940nm + transistor → comando AC
 *
 * Pinagem:
 *   GPIO 21 (SDA) → BME280 SDA
 *   GPIO 22 (SCL) → BME280 SCL
 *   GPIO 13       → HC-SR501 OUT
 *   GPIO 4        → LED IR (via resistor 330Ω)
 *
 * Bibliotecas necessárias (Arduino IDE → Gerenciar Bibliotecas):
 *   - Adafruit BME280 Library (by Adafruit)
 *   - Adafruit Unified Sensor (by Adafruit)
 *   - PubSubClient (by Nick O'Leary)
 *   - ArduinoJson (by Benoit Blanchon) v6+
 *   - IRremoteESP8266 (by crankyoldgit) — apenas se usar IR real
 *
 * Placa: ESP32 Dev Module (Ferramentas → Placa → ESP32 Arduino → ESP32 Dev Module)
 * Upload Speed: 115200
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <Adafruit_Sensor.h>

// ─── CONFIGURAÇÃO — ALTERE ANTES DE FLASHAR ──────────────────────────────────

// Wi-Fi da rede local (mesma rede do notebook com Docker)
const char* WIFI_SSID     = "NOME_DA_REDE_WIFI";
const char* WIFI_PASSWORD = "SENHA_DO_WIFI";

// Broker MQTT
// OPÇÃO A — mesma rede Wi-Fi: descubra com `ipconfig` no notebook (IPv4 da Wi-Fi)
const char* MQTT_BROKER   = "192.168.1.100";  // << ALTERE para o IP do notebook
// OPÇÃO B — redes diferentes (ExpoTech via Ngrok): use o host TCP do Ngrok
// const char* MQTT_BROKER = "0.tcp.sa.ngrok.io";  // << host Ngrok

const int   MQTT_PORT     = 1883;
// Se usar Ngrok, substitua a porta pelo número que aparece em localhost:4040
// const int MQTT_PORT = 12345;

// Identificação deste dispositivo — aparece como "sala" no dashboard
const char* ROOM_ID       = "room-esp32";  // pode usar: room-101, room-202, etc.

// ─── PINOS ───────────────────────────────────────────────────────────────────

#define PIN_PIR    13   // HC-SR501 sinal
#define PIN_IR_LED  4   // LED IR (saída digital)
#define BME_SDA    21
#define BME_SCL    22

// ─── CONFIGURAÇÃO DE PUBLICAÇÃO ──────────────────────────────────────────────

const unsigned long PUBLISH_INTERVAL_MS = 5000;  // 5 segundos

// ─── TÓPICOS MQTT ────────────────────────────────────────────────────────────

char TOPIC_TEMP[64];
char TOPIC_UMID[64];
char TOPIC_PRES[64];
char TOPIC_CMD[64];   // recebe comandos do backend (ligar/desligar/setpoint)

// ─── OBJETOS ─────────────────────────────────────────────────────────────────

WiFiClient       wifiClient;
PubSubClient     mqttClient(wifiClient);
Adafruit_BME280  bme;

bool     bmeOk       = false;
uint32_t tick        = 0;
unsigned long lastPublish = 0;

// ─── CALLBACKS ───────────────────────────────────────────────────────────────

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Recebe comandos do backend: {"action":"on"|"off"|"setpoint","value":23.0}
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  StaticJsonDocument<128> doc;
  if (deserializeJson(doc, msg) != DeserializationError::Ok) return;

  const char* action = doc["action"] | "";
  float       value  = doc["value"]  | 0.0f;

  if (strcmp(action, "on") == 0) {
    // Aqui entra o código do IR para ligar o AC
    // IRsend irsend(PIN_IR_LED); irsend.sendNEC(0xXXXXXXXX, 32);
    digitalWrite(PIN_IR_LED, HIGH);
    delay(100);
    digitalWrite(PIN_IR_LED, LOW);
    Serial.printf("[CMD] Ligar AC\n");

  } else if (strcmp(action, "off") == 0) {
    digitalWrite(PIN_IR_LED, HIGH);
    delay(100);
    digitalWrite(PIN_IR_LED, LOW);
    Serial.printf("[CMD] Desligar AC\n");

  } else if (strcmp(action, "setpoint") == 0) {
    Serial.printf("[CMD] Setpoint → %.1f°C\n", value);
    // Enviar código IR específico do AC para o setpoint desejado
  }
}

// ─── CONECTIVIDADE ───────────────────────────────────────────────────────────

void connectWiFi() {
  Serial.printf("Conectando ao Wi-Fi: %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nWi-Fi OK! IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nFalha no Wi-Fi — reiniciando...");
    ESP.restart();
  }
}

void connectMQTT() {
  char clientId[32];
  snprintf(clientId, sizeof(clientId), "esp32-%s", ROOM_ID);

  Serial.printf("Conectando ao MQTT %s:%d ...\n", MQTT_BROKER, MQTT_PORT);

  int attempts = 0;
  while (!mqttClient.connected() && attempts < 5) {
    if (mqttClient.connect(clientId)) {
      Serial.println("MQTT OK!");
      mqttClient.subscribe(TOPIC_CMD);
      Serial.printf("Subscrito em: %s\n", TOPIC_CMD);
    } else {
      Serial.printf("MQTT falhou (estado=%d), tentando novamente...\n", mqttClient.state());
      delay(3000);
      attempts++;
    }
  }
}

// ─── PUBLICAÇÃO ──────────────────────────────────────────────────────────────

void publishSensorData() {
  // Timestamp simples (ms desde boot — o backend aceita ausência de timestamp)
  char timestamp[40];
  // Se tiver NTP configurado, use o tempo real. Por padrão, o backend preenche com UTC now.
  snprintf(timestamp, sizeof(timestamp), "");

  // ── Temperatura + Umidade (BME280) ──
  if (bmeOk) {
    float temp = bme.readTemperature();
    float umid = bme.readHumidity();

    // Validação básica (RN08 no backend também valida, mas filtramos aqui também)
    if (!isnan(temp) && temp >= 5.0 && temp <= 55.0) {
      StaticJsonDocument<192> doc;
      doc["value"]     = round(temp * 10.0f) / 10.0f;
      doc["tick"]      = tick;
      doc["sensor_id"] = String("temp-") + ROOM_ID;

      char buf[192];
      serializeJson(doc, buf);
      bool ok = mqttClient.publish(TOPIC_TEMP, buf, false);
      Serial.printf("[PUB] %s → %.1f°C %s\n", TOPIC_TEMP, temp, ok ? "OK" : "FALHOU");
    }

    if (!isnan(umid) && umid >= 5.0 && umid <= 100.0) {
      StaticJsonDocument<192> doc;
      doc["value"]     = round(umid * 10.0f) / 10.0f;
      doc["tick"]      = tick;
      doc["sensor_id"] = String("umid-") + ROOM_ID;

      char buf[192];
      serializeJson(doc, buf);
      mqttClient.publish(TOPIC_UMID, buf, false);
    }

  } else {
    // BME280 não encontrado — publica temperatura simulada para teste
    float fakeTemp = 22.0 + (tick % 10) * 0.3;
    StaticJsonDocument<128> doc;
    doc["value"]     = fakeTemp;
    doc["tick"]      = tick;
    doc["sensor_id"] = String("temp-") + ROOM_ID;
    char buf[128];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_TEMP, buf, false);
    Serial.printf("[PUB] SIMULADO %s → %.1f°C\n", TOPIC_TEMP, fakeTemp);
  }

  // ── Presença (HC-SR501) ──
  int presence = digitalRead(PIN_PIR);
  {
    StaticJsonDocument<128> doc;
    doc["value"]     = presence;   // 1 = detectado, 0 = ausente
    doc["tick"]      = tick;
    doc["sensor_id"] = String("pres-") + ROOM_ID;

    char buf[128];
    serializeJson(doc, buf);
    mqttClient.publish(TOPIC_PRES, buf, false);
    Serial.printf("[PUB] Presença: %s\n", presence ? "DETECTADA" : "ausente");
  }

  tick++;
}

// ─── SETUP ───────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Smart Building ESP32 Firmware ===");

  // Monta tópicos com o ROOM_ID
  snprintf(TOPIC_TEMP, sizeof(TOPIC_TEMP), "sensors/room/%s/temperature", ROOM_ID);
  snprintf(TOPIC_UMID, sizeof(TOPIC_UMID), "sensors/room/%s/humidity",    ROOM_ID);
  snprintf(TOPIC_PRES, sizeof(TOPIC_PRES), "sensors/room/%s/presence",    ROOM_ID);
  snprintf(TOPIC_CMD,  sizeof(TOPIC_CMD),  "devices/ac/%s/commands",      ROOM_ID);

  Serial.printf("Room ID  : %s\n", ROOM_ID);
  Serial.printf("Temp     : %s\n", TOPIC_TEMP);
  Serial.printf("Umidade  : %s\n", TOPIC_UMID);
  Serial.printf("Presença : %s\n", TOPIC_PRES);
  Serial.printf("Comandos : %s\n", TOPIC_CMD);

  // Pinos
  pinMode(PIN_PIR,    INPUT);
  pinMode(PIN_IR_LED, OUTPUT);
  digitalWrite(PIN_IR_LED, LOW);

  // BME280
  Wire.begin(BME_SDA, BME_SCL);
  bmeOk = bme.begin(0x76);
  if (!bmeOk) bmeOk = bme.begin(0x77);  // endereço alternativo
  if (bmeOk) {
    Serial.println("BME280 detectado OK");
  } else {
    Serial.println("BME280 NAO encontrado — modo simulado ativado");
  }

  // Rede
  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
  mqttClient.setBufferSize(512);
  connectMQTT();

  Serial.println("Setup concluído — iniciando publicação...\n");
}

// ─── LOOP ────────────────────────────────────────────────────────────────────

void loop() {
  // Reconexão automática
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi perdido — reconectando...");
    connectWiFi();
  }
  if (!mqttClient.connected()) {
    Serial.println("MQTT desconectado — reconectando...");
    connectMQTT();
  }

  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;
    publishSensorData();
  }
}
