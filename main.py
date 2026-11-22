"""RF4 Spot-Datenbank – lokale App mit Web-Oberfläche.

Start:  python main.py   (oder start.bat)
Daten:  Ordner 'daten' neben dieser Datei (spots.db + bilder/)

Die Oberfläche läuft in einem eigenen Fenster (pywebview). Ist pywebview nicht
installiert, öffnet sich die App stattdessen im Standard-Browser.
"""
import sys
import threading
import webbrowser
from pathlib import Path

from server import starte_server

if getattr(sys, "frozen", False):
    # Als .exe (PyInstaller): Daten neben der .exe, Oberfläche aus dem Paket
    APP_DIR = Path(sys.executable).resolve().parent
    RES_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RES_DIR = APP_DIR
DATA_DIR = APP_DIR / "daten"
WEB_DIR = RES_DIR / "web"
ICON = RES_DIR / "app.ico"

# Gewässer aus RF4 – hier einfach ergänzen/umbenennen
GEWAESSER = [
    "Mosquito Lake",
    "Winding Rivulet",
    "Old Burg Lake",
    "Belaya River",
    "Kuori Lake",
    "Bear Lake",
    "Volkhov River",
    "Northern Donets River",
    "Sura River",
    "Ladoga Lake",
    "Amber Lake",
    "Ladoga Archipelago",
    "Akhtuba River",
    "Copper Lake",
    "Lower Tunguska River",
    "Yama River",
    "Norwegian Sea",
]


def main():
    server, url = starte_server(DATA_DIR, WEB_DIR, GEWAESSER)

    try:
        import webview
    except ImportError:
        print("pywebview ist nicht installiert – die App öffnet sich im Browser.")
        print("Für ein eigenes Fenster:  pip install pywebview")
        print(f"Adresse: {url}   (Beenden mit Strg+C)")
        webbrowser.open(url)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        server.shutdown()
        return

    webview.create_window(
        "RF4 Spot-Datenbank", url,
        width=1500, height=900, min_size=(1000, 650),
        maximized=True, background_color="#0B0E13",
    )
    webview.start(icon=str(ICON))
    server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
