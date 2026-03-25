import random
import time
import json
from datetime import datetime

# ============================================================
# KONFIGURATION — Schwellenwerte hier anpassen
# ============================================================

TEMP_ZU_HOCH   = 28.0   # °C  → Fan geht AN
TEMP_ZU_KALT   = 15.0   # °C  → Fan bleibt definitiv AUS
PUMPEN_DAUER   = 3      # Sekunden — wie lange pumpt die Pumpe?


# ============================================================
# SENSOR-SCHICHT (Später: echte DHT22 + Bodenfeuchtesensor)
# ============================================================

def read_sensors():
    """
    MOCK-VERSION: Zufällige Testdaten.
    Später einfach durch echte Sensor-Befehle ersetzen.
    """
    temperatur       = round(random.uniform(12.0, 35.0), 1)
    luftfeuchtigkeit = round(random.uniform(40.0, 85.0), 1)
    boden_nass       = random.choice([True, False])
    return temperatur, luftfeuchtigkeit, boden_nass


# ============================================================
# AKTOR-SCHICHT (Später: echte GPIO-Befehle)
# ============================================================

def pumpe_an(sekunden):
    """Pumpe einschalten für X Sekunden."""
    print(f"   🚿 PUMPE AN für {sekunden} Sekunden...")
    time.sleep(sekunden)
    print(f"   🚿 PUMPE AUS")

def fan_an():
    """Fan einschalten."""
    print("   💨 FAN AN — Temperatur wird reguliert")

def fan_aus():
    """Fan ausschalten."""
    print("   💨 FAN AUS")


# ============================================================
# STEUERUNGSLOGIK (Bleibt gleich — egal ob Mock oder Echt)
# ============================================================

def steuerung(temp, luft, boden_nass):
    """
    Entscheidungslogik für alle Aktoren.
    Gibt eine Zusammenfassung der Aktionen zurück.
    """
    aktionen = []

    # --- FAN-STEUERUNG ---
    if temp > TEMP_ZU_HOCH:
        fan_an()
        aktionen.append(f"Fan AN (Temp {temp}°C > {TEMP_ZU_HOCH}°C)")
    elif temp < TEMP_ZU_KALT:
        fan_aus()
        aktionen.append(f"Fan AUS (Temp {temp}°C < {TEMP_ZU_KALT}°C — zu kalt)")
    else:
        fan_aus()
        aktionen.append(f"Fan AUS (Temperatur {temp}°C ist OK)")

    # --- PUMPEN-STEUERUNG ---
    if not boden_nass:
        pumpe_an(PUMPEN_DAUER)
        aktionen.append(f"Pumpe AN für {PUMPEN_DAUER}s (Boden trocken)")
    else:
        aktionen.append("Pumpe AUS (Boden feucht genug)")
        print("   ✅ Boden feucht genug – Pumpe bleibt aus")

    return aktionen


# ============================================================
# DATEI-SCHNITTSTELLE (Für Person 4 / Node-RED Dashboard)
# ============================================================

def daten_speichern(temp, luft, boden_nass, aktionen):
    daten = {
        "zeit":             datetime.now().strftime("%H:%M:%S"),
        "temperatur":       temp,
        "luftfeuchtigkeit": luft,
        "boden_nass":       boden_nass,
        "aktionen":         aktionen
    }
    with open("sensordaten.json", "w") as f:
        json.dump(daten, f, indent=4)


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():
    print("🌱 Gewächshaussteuerung gestartet... (Beenden: Ctrl+C)\n")
    print(f"⚙️  Konfiguration: Fan AN bei >{TEMP_ZU_HOCH}°C | "
          f"Fan AUS bei <{TEMP_ZU_KALT}°C | "
          f"Pumpe läuft {PUMPEN_DAUER}s\n")

    while True:
        temp, luft, boden = read_sensors()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"🌡️  {temp}°C | 💧 {luft}% Luftfeuchte | "
              f"🪴 Boden nass: {boden}")

        aktionen = steuerung(temp, luft, boden)
        daten_speichern(temp, luft, boden, aktionen)

        print("-" * 55)
        time.sleep(5)

if __name__ == "__main__":
    main()
