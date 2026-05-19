"""
main.py — Smart Greenhouse Steuerung v2.0
==========================================
Hauptprogramm — orchestriert Sensoren, Steuerlogik und Aktoren.
EVA-Prinzip: Eingabe → Verarbeitung → Ausgabe

Autoren: Scata · Jacobs · Sickenberger · Vichigov
"""

import sys
import time
import logging
from pathlib import Path

# ============================================================
# KONFIGURATION — Hier alle Parameter anpassen
# ============================================================

MOCK_MODE      = True    # True = Testbetrieb | False = Echter Pi + ESP32

TEMP_ZU_HOCH   = 28.0   # °C → Lüfter AN
TEMP_ZU_KALT   = 15.0   # °C → Lüfter AUS (zu kalt)
PUMPEN_DAUER   = 3       # Sekunden Pumpenlaufzeit pro Zyklus
MESS_INTERVALL = 5       # Sekunden zwischen Messungen

# Serieller Port des ESP32 am Raspberry Pi
# Prüfen mit: ls /dev/ttyUSB* oder ls /dev/ttyACM*
SERIAL_PORT    = "/dev/ttyUSB0"
SERIAL_BAUD    = 115200

LOG_DATEI      = Path(__file__).parent.parent / "data" / "gewaechshaus.log"

# ============================================================
# LOGGING SETUP
# ============================================================

LOG_DATEI.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DATEI, encoding="utf-8"),
    ],
)
log = logging.getLogger("gewaechshaus")

# ============================================================
# MODULE LADEN
# ============================================================

import sensoren as sens
import daten

if MOCK_MODE:
    # Mock-Aktoren (kein GPIO nötig)
    from aktoren import luefter_an_mock  as luefter_an
    from aktoren import luefter_aus_mock as luefter_aus
    from aktoren import pumpe_an_mock    as pumpe_an
    gpio_init    = lambda: None
    gpio_cleanup = lambda: None
else:
    # Echte GPIO-Aktoren
    from aktoren import (
        luefter_an, luefter_aus, pumpe_an,
        gpio_initialisieren as gpio_init,
        gpio_aufraumen      as gpio_cleanup,
    )

# ============================================================
# STEUERUNGSLOGIK (EVA — Verarbeitung)
# ============================================================

def steuerung(werte: sens.Messwerte) -> list[str]:
    """
    Entscheidet anhand der Messwerte welche Aktoren geschaltet werden.

    Args:
        werte: Aktuelle Messwerte vom Sensor

    Returns:
        Liste der ausgeführten Aktionen (für Logging & Dashboard)
    """
    aktionen = []

    # --- LÜFTER ---
    if werte.temperatur > TEMP_ZU_HOCH:
        luefter_an()
        aktionen.append(f"Lüfter AN (Temp {werte.temperatur}°C > {TEMP_ZU_HOCH}°C)")

    elif werte.temperatur < TEMP_ZU_KALT:
        luefter_aus()
        aktionen.append(f"Lüfter AUS (Temp {werte.temperatur}°C < {TEMP_ZU_KALT}°C — zu kalt)")

    else:
        luefter_aus()
        aktionen.append(f"Lüfter AUS (Temp {werte.temperatur}°C ist OK)")

    # --- PUMPE ---
    if not werte.boden_nass:
        pumpe_an(PUMPEN_DAUER)
        aktionen.append(f"Pumpe AN für {PUMPEN_DAUER}s (Boden trocken, Rohwert: {werte.boden_roh})")
    else:
        aktionen.append(f"Pumpe AUS (Boden feucht genug, Rohwert: {werte.boden_roh})")
        log.info("✅ Boden feucht genug — Pumpe bleibt aus")

    return aktionen

# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main() -> None:
    modus_text = "🧪 MOCK-MODUS (Testdaten)" if MOCK_MODE else "✅ ECHTBETRIEB (Hardware)"

    log.info("=" * 60)
    log.info("🌱  Smart Greenhouse — Steuerung gestartet")
    log.info(f"    Modus:        {modus_text}")
    log.info(f"    Lüfter AN:    > {TEMP_ZU_HOCH}°C")
    log.info(f"    Lüfter AUS:   < {TEMP_ZU_KALT}°C")
    log.info(f"    Pumpendauer:  {PUMPEN_DAUER}s")
    log.info(f"    Intervall:    {MESS_INTERVALL}s")
    log.info(f"    Log-Datei:    {LOG_DATEI}")
    log.info("    Beenden mit Ctrl+C")
    log.info("=" * 60)

    # GPIO initialisieren (nur im Echtbetrieb)
    gpio_init()

    # Serial-Verbindung zum ESP32 öffnen (nur im Echtbetrieb)
    serial_port = None
    if not MOCK_MODE:
        try:
            import serial
            serial_port = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=10)
            log.info(f"📡 Serial verbunden: {SERIAL_PORT} @ {SERIAL_BAUD} Baud")
            time.sleep(2)  # ESP32 braucht kurz zum Starten
        except Exception as e:
            log.critical(f"❌ Serial-Port konnte nicht geöffnet werden: {e}")
            log.critical("   Prüfe: ls /dev/ttyUSB* | Kabel eingesteckt?")
            sys.exit(1)

    fehler_zaehler = 0
    MAX_FEHLER = 5  # Nach 5 aufeinanderfolgenden Fehlern: Warnung

    try:
        while True:
            try:
                # E — Eingabe: Sensoren lesen
                werte = sens.read_sensors(mock=MOCK_MODE, serial_port=serial_port)

                log.info(
                    f"🌡️  {werte.temperatur}°C  |  "
                    f"💧 {werte.luftfeuchtigkeit}% Luft  |  "
                    f"🪴 Boden: {'nass' if werte.boden_nass else 'TROCKEN'} "
                    f"(Rohwert: {werte.boden_roh})"
                )

                # V+A — Verarbeitung + Ausgabe: Aktoren schalten
                aktionen = steuerung(werte)

                # Daten speichern (für Node-RED Dashboard)
                daten.speichern(werte, aktionen, MOCK_MODE)

                fehler_zaehler = 0  # Reset bei Erfolg

            except RuntimeError as e:
                fehler_zaehler += 1
                log.error(f"❌ Sensorfehler ({fehler_zaehler}): {e}")

                if fehler_zaehler >= MAX_FEHLER:
                    log.warning(
                        f"⚠️  {MAX_FEHLER} Fehler in Folge! "
                        "Prüfe ESP32-Verbindung und Kabel."
                    )

            log.info("-" * 60)
            time.sleep(MESS_INTERVALL)

    except KeyboardInterrupt:
        log.info("\n🛑 Steuerung beendet (Ctrl+C)")

    finally:
        # Immer aufräumen — auch bei Absturz
        if serial_port and serial_port.is_open:
            serial_port.close()
            log.info("📡 Serial-Verbindung geschlossen")
        gpio_cleanup()
        log.info("✅ Sauber beendet")


if __name__ == "__main__":
    main()
