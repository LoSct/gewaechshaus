"""
dashboard.py — Smart Greenhouse Web-Dashboard
==============================================
Startet einen kleinen Webserver der die Sensordaten live anzeigt.
Starten mit: python3 dashboard.py
Dann im Browser öffnen: http://localhost:8080
"""

import json
import http.server
import socketserver
from pathlib import Path

PORT = 8080
DATEN_DATEI = Path(__file__).parent / "data" / "sensordaten.json"

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Greenhouse</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f1117; color: #e8e8e8; min-height: 100vh; padding: 2rem; }
  h1 { font-size: 1.4rem; font-weight: 500; color: #4ade80; margin-bottom: 0.25rem; }
  .subtitle { font-size: 0.8rem; color: #555; margin-bottom: 2rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
  .card { background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 12px; padding: 1.25rem; }
  .card-label { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
  .card-value { font-size: 2rem; font-weight: 500; }
  .card-unit { font-size: 0.9rem; color: #555; margin-left: 2px; }
  .temp { color: #fb923c; }
  .luft { color: #60a5fa; }
  .boden { color: #4ade80; }
  .status-an  { color: #4ade80; }
  .status-aus { color: #ef4444; }
  .aktionen { background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 12px; padding: 1.25rem; margin-bottom: 2rem; }
  .aktionen h2 { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; font-weight: 400; }
  .aktion { font-size: 0.85rem; color: #aaa; padding: 0.4rem 0; border-bottom: 1px solid #2a2d3a; }
  .aktion:last-child { border-bottom: none; }
  .verlauf { background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 12px; padding: 1.25rem; }
  .verlauf h2 { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; font-weight: 400; }
  table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  th { color: #555; font-weight: 400; text-align: left; padding: 0.4rem 0.5rem; border-bottom: 1px solid #2a2d3a; }
  td { color: #aaa; padding: 0.4rem 0.5rem; border-bottom: 1px solid #1a1d27; }
  tr:last-child td { border-bottom: none; }
  .update { font-size: 0.75rem; color: #444; text-align: right; margin-top: 1.5rem; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #4ade80; margin-right: 6px; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .mock-badge { display: inline-block; font-size: 0.7rem; background: #2a2d3a; color: #666; padding: 2px 8px; border-radius: 4px; margin-left: 8px; vertical-align: middle; }
</style>
</head>
<body>
<h1>🌱 Smart Greenhouse <span class="mock-badge" id="mock-badge"></span></h1>
<p class="subtitle"><span class="dot"></span>Live-Daten — aktualisiert alle 5 Sekunden</p>

<div class="grid">
  <div class="card">
    <div class="card-label">Temperatur</div>
    <div class="card-value temp" id="temp">—<span class="card-unit">°C</span></div>
  </div>
  <div class="card">
    <div class="card-label">Luftfeuchtigkeit</div>
    <div class="card-value luft" id="luft">—<span class="card-unit">%</span></div>
  </div>
  <div class="card">
    <div class="card-label">Bodenfeuchte</div>
    <div class="card-value boden" id="boden">—</div>
  </div>
  <div class="card">
    <div class="card-label">Lüfter</div>
    <div class="card-value" id="luefter">—</div>
  </div>
  <div class="card">
    <div class="card-label">Pumpe</div>
    <div class="card-value" id="pumpe">—</div>
  </div>
  <div class="card">
    <div class="card-label">Letzte Messung</div>
    <div class="card-value" style="font-size:1.3rem; color:#aaa;" id="zeit">—</div>
  </div>
</div>

<div class="aktionen">
  <h2>Aktuelle Aktionen</h2>
  <div id="aktionen-liste"></div>
</div>

<div class="verlauf">
  <h2>Verlauf (letzte 10 Messungen)</h2>
  <table>
    <thead>
      <tr>
        <th>Zeit</th>
        <th>Temp °C</th>
        <th>Luft %</th>
        <th>Boden</th>
        <th>Lüfter</th>
        <th>Pumpe</th>
      </tr>
    </thead>
    <tbody id="verlauf-body"></tbody>
  </table>
</div>

<p class="update" id="last-update"></p>

<script>
async function laden() {
  try {
    const r = await fetch('/daten');
    const d = await r.json();
    const a = d.aktuell;

    document.getElementById('temp').innerHTML = a.temperatur + '<span class="card-unit">°C</span>';
    document.getElementById('luft').innerHTML = a.luftfeuchtigkeit + '<span class="card-unit">%</span>';
    document.getElementById('boden').textContent = a.boden_nass ? 'Feucht' : 'Trocken';
    document.getElementById('zeit').textContent = a.zeit;
    document.getElementById('mock-badge').textContent = a.mock_modus ? 'Mock-Modus' : 'Echtbetrieb';

    // Lüfter & Pumpe aus Aktionen ableiten
    const aktionen = a.aktionen || [];
    const luefter = aktionen.some(x => x.includes('Lüfter AN'));
    const pumpe   = aktionen.some(x => x.includes('Pumpe AN'));
    document.getElementById('luefter').innerHTML = luefter
      ? '<span class="status-an">AN</span>'
      : '<span class="status-aus">AUS</span>';
    document.getElementById('pumpe').innerHTML = pumpe
      ? '<span class="status-an">AN</span>'
      : '<span class="status-aus">AUS</span>';

    // Aktionen-Liste
    const al = document.getElementById('aktionen-liste');
    al.innerHTML = aktionen.map(a => `<div class="aktion">→ ${a}</div>`).join('');

    // Verlauf (letzte 10, neueste zuerst)
    const verlauf = (d.verlauf || []).slice(-10).reverse();
    const tb = document.getElementById('verlauf-body');
    tb.innerHTML = verlauf.map(v => {
      const akt = v.aktionen || [];
      const lf  = akt.some(x => x.includes('Lüfter AN')) ? '<span class="status-an">AN</span>' : '<span class="status-aus">AUS</span>';
      const pm  = akt.some(x => x.includes('Pumpe AN'))  ? '<span class="status-an">AN</span>' : '<span class="status-aus">AUS</span>';
      return `<tr>
        <td>${v.zeit}</td>
        <td>${v.temperatur}°C</td>
        <td>${v.luftfeuchtigkeit}%</td>
        <td>${v.boden_nass ? 'Feucht' : 'Trocken'}</td>
        <td>${lf}</td>
        <td>${pm}</td>
      </tr>`;
    }).join('');

    document.getElementById('last-update').textContent = 'Zuletzt geladen: ' + new Date().toLocaleTimeString('de-DE');
  } catch(e) {
    document.getElementById('last-update').textContent = 'Fehler beim Laden — läuft main.py?';
  }
}

laden();
setInterval(laden, 5000);
</script>
</body>
</html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())

        elif self.path == "/daten":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                self.wfile.write(DATEN_DATEI.read_bytes())
            except FileNotFoundError:
                self.wfile.write(b'{"error": "sensordaten.json nicht gefunden"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Kein Log-Spam im Terminal


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌱 Dashboard läuft auf http://localhost:{PORT}")
        print("   Beenden mit Ctrl+C")
        httpd.serve_forever()
