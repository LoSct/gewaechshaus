"""
sensoren.py — Sensor-Schicht
============================
Liest Messwerte vom ESP32 über die serielle USB-Verbindung.
Der ESP32 schickt alle 5 Sekunden ein JSON-Paket mit:
  { "temperatur": 23.5, "luftfeuchtigkeit": 65.0, "boden_roh": 1800 }

Im Mock-Modus werden zufällige Testwerte zurückgegeben.
"""

import json
import random
import logging
from dataclasses import dataclass

log = logging.getLogger("gewaechshaus.sensoren")

# Schwellenwert für Bodenfeuchte-Rohwert (ESP32 ADC 0–4095)
# Unter diesem Wert gilt der Boden als NASS
BODEN_NASS_SCHWELLE = 2000  # Muss ggf. nach Kalibrierung angepasst werden


@dataclass
class Messwerte:
    """Enthält alle Sensorwerte eines Messzyklus."""
    temperatur: float        # °C
    luftfeuchtigkeit: float  # %
    boden_nass: bool         # True = Boden feucht, False = trocken
    boden_roh: int           # Rohwert des Bodensensors (0–4095)


def read_sensors(mock: bool = True, serial_port=None) -> Messwerte:
    """
    Liest alle Sensorwerte — entweder als Mock oder vom ESP32.

    Args:
        mock:        True = Zufällige Testdaten | False = Echter ESP32
        serial_port: Offener serial.Serial Port (nur bei mock=False nötig)

    Returns:
        Messwerte-Objekt mit allen Sensorwerten

    Raises:
        RuntimeError: Wenn ESP32 keine gültigen Daten schickt
    """
    if mock:
        return _mock_werte()
    return _echte_werte(serial_port)


def _mock_werte() -> Messwerte:
    """Generiert zufällige, realistische Testwerte."""
    boden_roh = random.randint(500, 4000)
    return Messwerte(
        temperatur=round(random.uniform(12.0, 35.0), 1),
        luftfeuchtigkeit=round(random.uniform(40.0, 85.0), 1),
        boden_nass=boden_roh < BODEN_NASS_SCHWELLE,
        boden_roh=boden_roh,
    )


def _echte_werte(serial_port) -> Messwerte:
    """
    Liest einen JSON-Datensatz vom ESP32 über Serial.

    Der ESP32 schickt kontinuierlich Zeilen wie:
        {"temperatur": 23.5, "luftfeuchtigkeit": 65.0, "boden_roh": 1800}

    Raises:
        RuntimeError: Bei ungültigen oder fehlenden Daten
    """
    if serial_port is None:
        raise RuntimeError("Kein Serial-Port übergeben (serial_port=None)")

    try:
        # Lese eine Zeile vom ESP32 (blockiert bis Daten ankommen)
        zeile = serial_port.readline().decode("utf-8").strip()

        if not zeile:
            raise RuntimeError("Leere Antwort vom ESP32")

        daten = json.loads(zeile)

        # Pflichtfelder prüfen
        for feld in ("temperatur", "luftfeuchtigkeit", "boden_roh"):
            if feld not in daten:
                raise RuntimeError(f"Fehlendes Feld im ESP32-Paket: '{feld}'")

        boden_roh = int(daten["boden_roh"])

        return Messwerte(
            temperatur=round(float(daten["temperatur"]), 1),
            luftfeuchtigkeit=round(float(daten["luftfeuchtigkeit"]), 1),
            boden_nass=boden_roh < BODEN_NASS_SCHWELLE,
            boden_roh=boden_roh,
        )

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Ungültiges JSON vom ESP32: {e}") from e
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"Fehler beim Lesen der Sensordaten: {e}") from e
