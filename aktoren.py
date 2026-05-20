"""
aktoren.py — Aktor-Schicht
===========================
Steuert Lüfter und Pumpe über das 2-Kanal-Relaismodul am Raspberry Pi 5.

Relais-Logik (aktiv LOW — Standard bei den meisten Modulen):
  GPIO.LOW  → Relais GESCHLOSSEN → Aktor AN
  GPIO.HIGH → Relais OFFEN      → Aktor AUS

Pin-Belegung (BCM-Nummerierung):
  GPIO 17 → Relais-Kanal 1 → Lüfter
  GPIO 27 → Relais-Kanal 2 → Pumpe
"""

import time
import logging

log = logging.getLogger("gewaechshaus.aktoren")

# GPIO-Pin Belegung (BCM-Nummern)
PIN_LUEFTER = 17
PIN_PUMPE   = 27

# Aktiv-LOW: True = Relais schalten mit LOW-Signal (Standard)
AKTIV_LOW = True


def gpio_initialisieren() -> None:
    """
    Initialisiert alle GPIO-Pins als Outputs.
    Muss einmal beim Programmstart aufgerufen werden.
    Startet mit beiden Aktoren AUS (sicherer Ausgangszustand).
    """
    import lgpio as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(PIN_LUEFTER, GPIO.OUT)
    GPIO.setup(PIN_PUMPE,   GPIO.OUT)

    # Sicherer Startzustand: beide Aktoren AUS
    _setze_pin(PIN_LUEFTER, False)
    _setze_pin(PIN_PUMPE,   False)

    log.info(f"GPIO initialisiert — Pin {PIN_LUEFTER} (Lüfter), Pin {PIN_PUMPE} (Pumpe)")


def gpio_aufraumen() -> None:
    """Gibt alle GPIO-Pins frei. Immer beim Programmende aufrufen."""
    import RPi.GPIO as GPIO
    _setze_pin(PIN_LUEFTER, False)  # Sicherheitshalber AUS
    _setze_pin(PIN_PUMPE,   False)
    GPIO.cleanup()
    log.info("GPIO aufgeräumt")


def _setze_pin(pin: int, an: bool) -> None:
    """
    Setzt einen GPIO-Pin unter Berücksichtigung der Relais-Logik.

    Args:
        pin: BCM-Pinnummer
        an:  True = Aktor einschalten, False = Aktor ausschalten
    """
    import RPi.GPIO as GPIO
    if AKTIV_LOW:
        GPIO.output(pin, GPIO.LOW if an else GPIO.HIGH)
    else:
        GPIO.output(pin, GPIO.HIGH if an else GPIO.LOW)


# ---- Lüfter ----

def luefter_an() -> None:
    """Lüfter einschalten."""
    _setze_pin(PIN_LUEFTER, True)
    log.info("💨 LÜFTER AN")


def luefter_aus() -> None:
    """Lüfter ausschalten."""
    _setze_pin(PIN_LUEFTER, False)
    log.info("💨 LÜFTER AUS")


# ---- Pumpe ----

def pumpe_an(sekunden: int) -> None:
    """
    Pumpe für eine definierte Zeit einschalten, dann automatisch ausschalten.

    Args:
        sekunden: Pumpenlaufzeit in Sekunden
    """
    _setze_pin(PIN_PUMPE, True)
    log.info(f"🚿 PUMPE AN für {sekunden} Sekunden...")
    time.sleep(sekunden)
    _setze_pin(PIN_PUMPE, False)
    log.info("🚿 PUMPE AUS")


# ---- Mock-Versionen (ohne GPIO) ----

def luefter_an_mock() -> None:
    log.info("💨 [MOCK] LÜFTER AN")

def luefter_aus_mock() -> None:
    log.info("💨 [MOCK] LÜFTER AUS")

def pumpe_an_mock(sekunden: int) -> None:
    log.info(f"🚿 [MOCK] PUMPE AN für {sekunden} Sekunden...")
    time.sleep(sekunden)
    log.info("🚿 [MOCK] PUMPE AUS")
