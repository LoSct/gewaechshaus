# 🌱 Smart Greenhouse

> Automatische Gewächshaussteuerung mit IoT-Technologie  
> Raspberry Pi 5 · ESP32 · DHT11 · Node-RED Dashboard

**Autoren:** Lorenzo Scata · Marvin Jacobs · Sebastian Sickenberger · Hamsat Vichigov  
**Projekt:** netgo intern

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Systemarchitektur](#systemarchitektur)
3. [Hardware & Verkabelung](#hardware--verkabelung)
4. [Schnellstart](#schnellstart)
5. [ESP32 flashen](#esp32-flashen)
6. [Raspberry Pi einrichten](#raspberry-pi-einrichten)
7. [Vom Mock- in den Echtbetrieb wechseln](#vom-mock--in-den-echtbetrieb-wechseln)
8. [Node-RED Dashboard](#node-red-dashboard)
9. [Projektstruktur](#projektstruktur)
10. [Konfiguration](#konfiguration)
11. [Fehlerbehebung](#fehlerbehebung)

---

## Überblick

Das Smart Greenhouse ist ein vollautomatisches Steuerungssystem für ein Gewächshaus. Es erfasst Umweltdaten (Temperatur, Luftfeuchtigkeit, Bodenfeuchte) und steuert auf Basis dieser Daten einen Lüfter und eine Wasserpumpe — ohne manuellen Eingriff.

**Steuerlogik (EVA-Prinzip):**

| Sensor | Messgröße | Aktion |
|--------|-----------|--------|
| DHT11 | Temperatur > 28°C | Lüfter AN |
| DHT11 | Temperatur < 15°C | Lüfter AUS |
| Bodensensor | Boden trocken | Pumpe AN (3s) |
| Bodensensor | Boden feucht | Pumpe AUS |

---

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5                        │
│                                                          │
│   main.py                                                │
│   ┌──────────┐   ┌────────────┐   ┌──────────────────┐  │
│   │sensoren.py│→ │  main.py   │→  │   aktoren.py     │  │
│   │(Serial)  │   │(Steuerung) │   │(GPIO → Relais)   │  │
│   └──────────┘   └─────┬──────┘   └──────────────────┘  │
│                         │                    │            │
│                   daten.py              GPIO 17 / 27      │
│                  sensordaten.json            │            │
│                  (→ Node-RED)                │            │
└──────────────────────────────────────────────┼───────────┘
                                               │
                                    ┌──────────┴──────────┐
           USB / Serial             │    Relais-Modul      │
┌──────────────────────┐            │   Kanal 1: Lüfter   │
│       ESP32          │            │   Kanal 2: Pumpe    │
│                      │            └─────────────────────┘
│  DHT11 → GPIO4       │
│  Bodensensor → GPIO34│
└──────────────────────┘
```

**Kommunikationsweg:**
1. ESP32 liest DHT11 + Bodensensor alle 5 Sekunden
2. ESP32 sendet JSON per USB-Serial an den Pi
3. Pi verarbeitet Daten und steuert Relais via GPIO
4. Pi speichert Daten in `sensordaten.json` für Node-RED

---

## Hardware & Verkabelung

### Komponenten

| Bauteil | Beschreibung |
|---------|-------------|
| Raspberry Pi 5 | Zentraleinheit, läuft Python-Steuerungscode |
| ESP32 | Sensor-Interface, liest DHT11 + Bodensensor |
| DHT11 | Temperatur + Luftfeuchtigkeit |
| Kapazitiver Bodensensor | Bodenfeuchte (korrosionsfrei) |
| 2-Kanal Relaismodul | Schaltet Lüfter und Pumpe |
| 12V Lüfter | Belüftung und Temperaturregelung |
| Wasserpumpe | Bewässerung |
| Externe Netzteile | Stromversorgung für Aktoren |

---

### ESP32 Verkabelung

```
ESP32                DHT11
─────────────────────────────
GPIO 4       →       DATA
3.3V         →       VCC
GND          →       GND

ESP32                Kapazitiver Bodensensor
─────────────────────────────────────────────
GPIO 34 (ADC)→       AOUT (Analogausgang)
3.3V         →       VCC
GND          →       GND

ESP32                Raspberry Pi
─────────────────────────────────
USB-Kabel    →       USB-Port
(Serial-Kommunikation über USB)
```

> ⚠️ **Wichtig:** GPIO 34–39 am ESP32 sind reine Eingänge (kein Pull-up/down intern). Für den Bodensensor perfekt geeignet.

---

### Raspberry Pi Verkabelung

```
Raspberry Pi 5 (BCM)     2-Kanal Relaismodul
────────────────────────────────────────────
GPIO 17  (Pin 11) →      IN1 (Lüfter)
GPIO 27  (Pin 13) →      IN2 (Pumpe)
5V       (Pin 2)  →      VCC
GND      (Pin 6)  →      GND

Relaismodul              Lüfter / Pumpe
────────────────────────────────────────────
COM1 + NO1        →      Lüfter (12V)
COM2 + NO2        →      Pumpe
(Externes Netzteil für 12V!)
```

> ⚠️ **Galvanische Trennung:** Das Relaismodul trennt die 3.3V GPIO-Logik vom 12V Hochstromkreis. Niemals 12V direkt an GPIO anschließen!

> ⚠️ **Wasser & Elektronik:** Raspberry Pi und ESP32 physisch von Wasseranschlüssen fernhalten!

---

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/LoSct/gewaechshaus.git
cd gewaechshaus

# 2. Setup ausführen (installiert Pakete, richtet Serial ein)
bash setup.sh

# 3. Im Mock-Modus testen (kein Hardware nötig)
python3 src/main.py

# 4. Nach Hardware-Aufbau: Echtbetrieb aktivieren
#    → MOCK_MODE = False in src/main.py setzen
python3 src/main.py
```

---

## ESP32 flashen

### Voraussetzungen
- [Arduino IDE](https://www.arduino.cc/en/software) installiert
- ESP32-Board-Support installiert:
  - Arduino IDE → Datei → Einstellungen → Zusätzliche Boardverwalter-URLs:
    ```
    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
    ```
  - Werkzeuge → Board → Boardverwalter → `esp32` suchen → Installieren

### Bibliotheken installieren
Arduino IDE → Werkzeuge → Bibliotheken verwalten:
- `DHT sensor library` von Adafruit → Installieren (inkl. Abhängigkeiten)
- `ArduinoJson` von Benoit Blanchon → Installieren

### Flashen
1. `esp32/esp32_sensors.ino` in Arduino IDE öffnen
2. Werkzeuge → Board → `ESP32 Dev Module`
3. Werkzeuge → Port → ESP32-Port auswählen (z.B. `/dev/ttyUSB0`)
4. Hochladen (→ Pfeil-Button)
5. Seriellen Monitor öffnen (115200 Baud) — JSON sollte erscheinen:
   ```json
   {"temperatur": "23.5", "luftfeuchtigkeit": "65.0", "boden_roh": 1800}
   ```

---

## Raspberry Pi einrichten

### SSH-Verbindung (vom Mac)
```bash
ssh pi@<IP-Adresse-des-Pi>
# IP-Adresse: im Router nachschauen oder am Pi mit: hostname -I
```

### Repository auf den Pi laden
```bash
git clone https://github.com/LoSct/gewaechshaus.git
cd gewaechshaus
bash setup.sh
```

### ESP32 Port prüfen
```bash
# ESP32 anschließen, dann:
ls /dev/ttyUSB*    # meist ttyUSB0
# oder:
ls /dev/ttyACM*    # bei manchen ESP32-Varianten ttyACM0
```

Falls `/dev/ttyACM0`: `SERIAL_PORT` in `src/main.py` entsprechend anpassen.

### Steuerung starten
```bash
python3 src/main.py
```

### Autostart beim Pi-Hochfahren einrichten (optional)
```bash
# Als systemd-Service einrichten
sudo nano /etc/systemd/system/gewaechshaus.service
```

Inhalt:
```ini
[Unit]
Description=Smart Greenhouse Steuerung
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/gewaechshaus/src/main.py
WorkingDirectory=/home/pi/gewaechshaus
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable gewaechshaus
sudo systemctl start gewaechshaus
sudo systemctl status gewaechshaus  # Status prüfen
```

---

## Vom Mock- in den Echtbetrieb wechseln

In `src/main.py` **eine Zeile ändern**:

```python
# Vorher (Testbetrieb):
MOCK_MODE = True

# Nachher (Echtbetrieb):
MOCK_MODE = False
```

Das ist alles. Die gesamte restliche Logik bleibt unverändert.

---

## Node-RED Dashboard

Das Programm schreibt alle Daten in `data/sensordaten.json`. Node-RED liest diese Datei und zeigt sie im Dashboard an.

### Node-RED installieren (auf dem Pi)
```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
sudo systemctl enable nodered
sudo systemctl start nodered
```

Dashboard erreichbar unter: `http://<Pi-IP>:1880`

### JSON-Struktur für Node-RED

```json
{
  "aktuell": {
    "zeit": "14:32:05",
    "datum": "2025-05-19",
    "temperatur": 23.5,
    "luftfeuchtigkeit": 65.0,
    "boden_nass": true,
    "boden_roh": 1650,
    "aktionen": ["Lüfter AUS (Temp 23.5°C ist OK)", "Pumpe AUS (Boden feucht genug)"]
  },
  "verlauf": [ ... ]
}
```

**Empfohlene Node-RED Nodes:**
- `node-red-dashboard` — Gauge, Chart, Text-Anzeigen
- `node-red-node-ui-table` — Tabelle für Verlaufsdaten

---

## Projektstruktur

```
gewaechshaus/
│
├── src/
│   ├── main.py          # Hauptprogramm & Konfiguration
│   ├── sensoren.py      # Sensor-Schicht (ESP32 Serial / Mock)
│   ├── aktoren.py       # Aktor-Schicht (GPIO Relais / Mock)
│   └── daten.py         # Datenspeicherung (JSON)
│
├── esp32/
│   └── esp32_sensors.ino  # Arduino-Code für den ESP32
│
├── data/                  # Automatisch erstellt beim Start
│   ├── sensordaten.json   # Aktuelle Daten + Verlauf (→ Node-RED)
│   └── gewaechshaus.log   # Log-Datei
│
├── requirements.txt       # Python-Abhängigkeiten
├── setup.sh               # Einrichtungs-Skript für den Pi
└── README.md
```

---

## Konfiguration

Alle Parameter zentral in `src/main.py`:

| Parameter | Standard | Beschreibung |
|-----------|----------|-------------|
| `MOCK_MODE` | `True` | `True` = Testbetrieb, `False` = Echtbetrieb |
| `TEMP_ZU_HOCH` | `28.0` | °C ab dem der Lüfter angeht |
| `TEMP_ZU_KALT` | `15.0` | °C unter dem der Lüfter aus bleibt |
| `PUMPEN_DAUER` | `3` | Sekunden Pumpenlaufzeit pro Zyklus |
| `MESS_INTERVALL` | `5` | Sekunden zwischen Messungen |
| `SERIAL_PORT` | `/dev/ttyUSB0` | USB-Port des ESP32 am Pi |
| `SERIAL_BAUD` | `115200` | Baudrate (muss mit ESP32-Code übereinstimmen) |

Bodensensor-Schwellenwert in `src/sensoren.py`:

| Parameter | Standard | Beschreibung |
|-----------|----------|-------------|
| `BODEN_NASS_SCHWELLE` | `2000` | ESP32 ADC-Wert (0–4095). Unter diesem Wert = nass. Nach Kalibrierung anpassen! |

---

## Fehlerbehebung

### ❌ `No module named 'serial'`
```bash
pip install pyserial --break-system-packages
```

### ❌ `Permission denied: '/dev/ttyUSB0'`
```bash
sudo usermod -aG dialout $USER
# Danach ab- und wieder anmelden
```

### ❌ `No module named 'RPi'`
```bash
pip install RPi.GPIO --break-system-packages
```

### ❌ ESP32 schickt keine Daten
1. Seriellen Monitor in Arduino IDE öffnen (115200 Baud)
2. Prüfen ob JSON erscheint
3. Verkabelung DHT11 prüfen (DATA-Pin am richtigen GPIO?)
4. `SERIAL_PORT` in `main.py` korrekt? (`/dev/ttyUSB0` oder `/dev/ttyACM0`)

### ❌ Lüfter/Pumpe schaltet nicht
1. `MOCK_MODE = False` gesetzt?
2. GPIO-Pins korrekt? BCM-Nummerierung verwenden (nicht physische Pinnummer)
3. Relais-Modul mit 5V versorgt?
4. `AKTIV_LOW = True` in `aktoren.py` — passt das zu eurem Relaismodul?

### ❌ DHT11 liefert `nan`
- DHT11 braucht 2 Sekunden nach dem Einschalten
- Pullup-Widerstand (4.7kΩ–10kΩ) zwischen VCC und DATA empfohlen
- Kabel möglichst kurz halten (<1m)

---

## Ausblick

- [ ] KI-gestützte Pflanzenpflege (Anpassung der Schwellenwerte basierend auf Verlaufsdaten)
- [ ] Mehrere Sensorzonen (mehrere ESP32)
- [ ] Push-Benachrichtigungen bei kritischen Werten
- [ ] Wetterdaten-Integration (externe API)
- [ ] Robustes Gehäuse für dauerhaften Betrieb
