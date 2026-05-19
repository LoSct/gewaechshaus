"""
daten.py — Datenspeicherung
============================
Speichert Messwerte und Aktionen in einer JSON-Datei.
Die Datei ist direkt kompatibel mit Node-RED.

Struktur der sensordaten.json:
{
    "aktuell": { ... letzter Messzyklus ... },
    "verlauf": [ ... letzte MAX_EINTRAEGE Zyklen ... ]
}
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from sensoren import Messwerte

log = logging.getLogger("gewaechshaus.daten")

DATEN_DATEI  = Path(__file__).parent.parent / "data" / "sensordaten.json"
MAX_EINTRAEGE = 500  # Maximale Anzahl gespeicherter Zyklen (~41 min bei 5s Intervall)


def speichern(werte: Messwerte, aktionen: list[str], mock: bool) -> None:
    """
    Fügt einen neuen Messzyklus zur JSON-Datei hinzu.

    Args:
        werte:   Messwerte des aktuellen Zyklus
        aktionen: Liste der ausgeführten Aktionen
        mock:    Gibt an ob Testbetrieb aktiv ist
    """
    jetzt = datetime.now()

    eintrag = {
        "zeit":             jetzt.strftime("%H:%M:%S"),
        "datum":            jetzt.strftime("%Y-%m-%d"),
        "timestamp":        jetzt.isoformat(),
        "temperatur":       werte.temperatur,
        "luftfeuchtigkeit": werte.luftfeuchtigkeit,
        "boden_nass":       werte.boden_nass,
        "boden_roh":        werte.boden_roh,
        "aktionen":         aktionen,
        "mock_modus":       mock,
    }

    # Bestehenden Verlauf laden
    verlauf = _verlauf_laden()

    # Neuen Eintrag anhängen und auf Maximum begrenzen
    verlauf.append(eintrag)
    if len(verlauf) > MAX_EINTRAEGE:
        verlauf = verlauf[-MAX_EINTRAEGE:]

    # Speichern
    ausgabe = {
        "aktuell": eintrag,
        "verlauf": verlauf,
    }

    DATEN_DATEI.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(DATEN_DATEI, "w", encoding="utf-8") as f:
            json.dump(ausgabe, f, indent=4, ensure_ascii=False)
    except OSError as e:
        log.error(f"❌ Fehler beim Speichern der Daten: {e}")


def _verlauf_laden() -> list:
    """Lädt den bisherigen Verlauf aus der JSON-Datei."""
    if not DATEN_DATEI.exists():
        return []

    try:
        with open(DATEN_DATEI, "r", encoding="utf-8") as f:
            inhalt = json.load(f)
            return inhalt.get("verlauf", [])
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"⚠️  Verlauf konnte nicht geladen werden ({e}) — starte neu")
        return []
