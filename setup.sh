#!/bin/bash
# ============================================================
# setup.sh — Einrichtung des Smart Greenhouse auf dem Raspberry Pi
# Ausführen mit: bash setup.sh
# ============================================================

set -e  # Bei Fehler sofort abbrechen

echo ""
echo "🌱 Smart Greenhouse — Setup"
echo "============================"
echo ""

# Python-Pakete installieren
echo "📦 Python-Pakete installieren..."
pip install -r requirements.txt --break-system-packages
echo "✅ Pakete installiert"
echo ""

# data/ Ordner anlegen (falls nicht vorhanden)
echo "📁 Verzeichnisse anlegen..."
mkdir -p data
echo "✅ data/ Ordner bereit"
echo ""

# Benutzer zur dialout-Gruppe hinzufügen (für Serial-Zugriff auf ESP32)
echo "🔌 Serial-Zugriff einrichten..."
if groups $USER | grep -q dialout; then
    echo "✅ Benutzer '$USER' ist bereits in der dialout-Gruppe"
else
    sudo usermod -aG dialout $USER
    echo "✅ Benutzer '$USER' zur dialout-Gruppe hinzugefügt"
    echo "⚠️  WICHTIG: Bitte einmal ab- und wieder anmelden damit die Gruppe aktiv wird!"
fi
echo ""

# ESP32 Port erkennen
echo "🔍 Suche nach ESP32..."
if ls /dev/ttyUSB* 2>/dev/null; then
    echo "✅ ESP32 gefunden (ttyUSB)"
elif ls /dev/ttyACM* 2>/dev/null; then
    echo "✅ ESP32 gefunden (ttyACM)"
    echo "ℹ️  Tipp: Passe SERIAL_PORT in src/main.py auf /dev/ttyACM0 an"
else
    echo "⚠️  Kein ESP32 gefunden — erst anschließen, dann nochmal prüfen mit: ls /dev/tty*"
fi
echo ""

echo "============================"
echo "✅ Setup abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "  1. ESP32 flashen: esp32/esp32_sensors.ino mit Arduino IDE öffnen"
echo "  2. MOCK_MODE = False setzen in src/main.py (wenn Hardware bereit)"
echo "  3. Starten mit: python3 src/main.py"
echo ""
