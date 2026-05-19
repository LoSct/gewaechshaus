/*
 * Smart Greenhouse — ESP32 Sensor-Interface
 * ==========================================
 * Liest DHT11 (Temperatur + Luftfeuchtigkeit) und
 * kapazitiven Bodenfeuchtesensor, sendet JSON per Serial an den Raspberry Pi.
 *
 * Ausgabe alle 5 Sekunden:
 *   {"temperatur": 23.5, "luftfeuchtigkeit": 65.0, "boden_roh": 1800}
 *
 * Autoren: Scata · Jacobs · Sickenberger · Vichigov
 *
 * Bibliotheken (Arduino IDE → Library Manager):
 *   - DHT sensor library by Adafruit
 *   - ArduinoJson by Benoit Blanchon
 */

#include <DHT.h>
#include <ArduinoJson.h>

// ============================================================
// PIN-BELEGUNG — Hier anpassen falls nötig
// ============================================================

#define DHT_PIN        4    // GPIO4 → DHT11 Datenpin
#define DHT_TYP        DHT11
#define BODEN_PIN      34   // GPIO34 → Analogeingang Bodenfeuchtesensor
                             // (GPIO34-39 sind reine Eingänge am ESP32)

// ============================================================
// KONFIGURATION
// ============================================================

#define MESS_INTERVALL_MS  5000   // Millisekunden zwischen Messungen
#define SERIAL_BAUD        115200
#define JSON_BUFFER_SIZE   128

// Anzahl der Messungen für gleitenden Mittelwert (Bodensensor)
#define MITTELWERT_N  5

// ============================================================
// OBJEKTE
// ============================================================

DHT dht(DHT_PIN, DHT_TYP);

// ============================================================
// SETUP
// ============================================================

void setup() {
  Serial.begin(SERIAL_BAUD);
  dht.begin();

  // Kurz warten bis DHT11 bereit ist
  delay(2000);

  Serial.println("# Smart Greenhouse ESP32 gestartet");
  Serial.print("# DHT_PIN: ");
  Serial.print(DHT_PIN);
  Serial.print(" | BODEN_PIN: ");
  Serial.println(BODEN_PIN);
}

// ============================================================
// HILFSFUNKTION: Gleitender Mittelwert Bodensensor
// ============================================================

int boden_mittelwert() {
  long summe = 0;
  for (int i = 0; i < MITTELWERT_N; i++) {
    summe += analogRead(BODEN_PIN);
    delay(10);
  }
  return (int)(summe / MITTELWERT_N);
}

// ============================================================
// HAUPTLOOP
// ============================================================

void loop() {
  // DHT11 auslesen
  float luftfeuchtigkeit = dht.readHumidity();
  float temperatur       = dht.readTemperature();  // Celsius

  // Bodensensor auslesen (Mittelwert für Stabilität)
  int boden_roh = boden_mittelwert();

  // Sensor-Fehlerprüfung
  if (isnan(luftfeuchtigkeit) || isnan(temperatur)) {
    // Fehler als Kommentarzeile senden (wird vom Pi ignoriert)
    Serial.println("# FEHLER: DHT11 liefert keine Daten — Verkabelung prüfen!");
    delay(MESS_INTERVALL_MS);
    return;
  }

  // JSON zusammenbauen und senden
  StaticJsonDocument<JSON_BUFFER_SIZE> doc;
  doc["temperatur"]       = serialized(String(temperatur, 1));
  doc["luftfeuchtigkeit"] = serialized(String(luftfeuchtigkeit, 1));
  doc["boden_roh"]        = boden_roh;

  serializeJson(doc, Serial);
  Serial.println();  // Zeilenende — wichtig für Pi readline()

  delay(MESS_INTERVALL_MS);
}
