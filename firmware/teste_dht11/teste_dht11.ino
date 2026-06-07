/**
 * Smart Building — Teste isolado do DHT11
 *
 * OBJETIVO: confirmar se o SENSOR DHT11 está vivo, separado do Arduino de
 * produção (que você NÃO deve regravar, pois não há backup do firmware).
 *
 * Use em: Arduino UNO RESERVA  ou  ESP32 reserva  (NÃO no Arduino do AC).
 *
 * Biblioteca: "DHT sensor library" (Adafruit) — instale pelo Library Manager,
 * junto com "Adafruit Unified Sensor".
 *
 * LIGAÇÃO (DHT11 de 4 pinos):
 *   DHT pino 1 (VCC)  → 5V (ou 3V3 no ESP32)
 *   DHT pino 2 (DATA) → DHT_PIN abaixo
 *   DHT pino 3 (NC)   → não conecta
 *   DHT pino 4 (GND)  → GND
 *   RESISTOR PULL-UP 4.7k–10k entre DATA e VCC  ← causa nº1 de "Erro DHT11"
 *   (módulos de 3 pinos / placa azul já têm o pull-up embutido)
 */

#include <DHT.h>

// ── Ajuste o pino conforme sua placa ────────────────────────────────────────
// Arduino UNO: um pino digital (ex.: 2). ESP32: um GPIO (ex.: 4).
#define DHT_PIN   2
#define DHT_TYPE  DHT11    // troque para DHT22 se o seu sensor for o azul maior

DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastRead = 0;
uint16_t okCount = 0;
uint16_t errCount = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Teste isolado DHT11 ===");
  Serial.printf("Pino DATA: %d | Tipo: DHT11\n", DHT_PIN);
  Serial.println("Lendo a cada 2.5 s (DHT11 nao aceita leituras mais rapidas).");
  dht.begin();
}

void loop() {
  // DHT11 precisa de >= 2 s entre leituras; usamos 2.5 s por margem.
  if (millis() - lastRead < 2500) return;
  lastRead = millis();

  float h = dht.readHumidity();
  float t = dht.readTemperature();   // Celsius

  if (isnan(h) || isnan(t)) {
    errCount++;
    Serial.printf("[ERRO] leitura falhou (NaN). ok=%u err=%u\n", okCount, errCount);
    Serial.println("       -> verifique pull-up, fiacao, jumpers e alimentacao.");
  } else {
    okCount++;
    Serial.printf("[OK] Temp=%.1f C | Umid=%.1f %% | ok=%u err=%u\n",
                  t, h, okCount, errCount);
  }
}
