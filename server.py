"""Lokaler Server (nur 127.0.0.1) zwischen Web-Oberfläche und SQLite-Datenbank.

Es gibt keine Verbindung ins Internet: der Server ist nur auf diesem PC erreichbar.
"""
import base64
import binascii
import json
import re
import threading
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from db import SPALTEN, SpotDB
from fischarten import FISCHARTEN

BILD_FELDER = ["bild_trophaee", "bild_montage", "bild_kescher"]
BILD_NAME = re.compile(r"^[0-9a-f]{32}\.(png|jpg|jpeg|gif|bmp|webp)$")
BILD_TYPEN = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/bmp": ".bmp", "image/webp": ".webp",
}
TROPHAEE_WERTE = ["Trophäe", "Seltene Trophäe"]
MAX_ANFRAGE = 150 * 1024 * 1024  # 3 Bilder als Base64 passen sicher hinein
MAX_TEXT = 500
MAX_NOTIZEN = 20000

STATISCH = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/logo.png": ("logo.png", "image/png"),
}
BILD_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp"}


class Fehler(Exception):
    """Fehler mit verständlicher Meldung für die Oberfläche."""

    def __init__(self, meldung, status=400):
        super().__init__(meldung)
        self.status = status


class SpotDienst:
    """Geschäftslogik: prüft Eingaben, speichert Bilder, spricht mit der DB."""

    def __init__(self, data_dir: Path, gewaesser: list):
        self.data_dir = data_dir
        self.img_dir = data_dir / "bilder"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.einstellungen_datei = data_dir / "einstellungen.json"
        self.gewaesser = gewaesser
        self.db = SpotDB(data_dir / "spots.db")
        self.lock = threading.Lock()

    # ---------- Lesen ----------
    def meta(self):
        with self.lock:
            eigene = [g for g in self.db.alle_gewaesser() if g not in self.gewaesser]
            # Ältere Einträge mit anderer Schreibweise: nur zum Filtern anbieten
            alt_fische = [f for f in self.db.alle_fischarten() if f not in FISCHARTEN]
        return {"gewaesser": self.gewaesser + sorted(eigene), "trophaeen": TROPHAEE_WERTE,
                "fischarten": FISCHARTEN, "fischarten_alt": alt_fische}

    def liste(self, filter_):
        with self.lock:
            zeilen = self.db.suchen(filter_.get("text", "").strip(),
                                    filter_.get("gewaesser", "").strip(),
                                    filter_.get("fischart", "").strip(),
                                    filter_.get("trophaee", "").strip())
        return [dict(z) for z in zeilen]

    def holen(self, spot_id):
        with self.lock:
            spot = self.db.holen(spot_id)
        if not spot:
            raise Fehler("Spot nicht gefunden.", 404)
        return dict(spot)

    # ---------- Schreiben ----------
    def speichern(self, daten, spot_id=None):
        alt = self.holen(spot_id) if spot_id else None
        sauber = self._pruefen(daten)
        fisch = sauber.get("fischart")
        # Nur Fischarten aus der Liste – ein bestehender Spot darf seine alte Schreibweise behalten
        if fisch and fisch not in FISCHARTEN and not (alt and alt["fischart"] == fisch):
            raise Fehler(f"Unbekannte Fischart: {fisch}. Bitte aus der Liste wählen.")

        # Bilder: vorhandenen Namen behalten, None = entfernt, data:-URL = neues Bild
        neu_geschrieben, zu_loeschen = [], []
        try:
            for feld in BILD_FELDER:
                wert = daten.get(feld)
                alter_name = alt[feld] if alt else None
                if isinstance(wert, str) and wert.startswith("data:"):
                    name = self._bild_schreiben(wert)
                    neu_geschrieben.append(name)
                    sauber[feld] = name
                    if alter_name:
                        zu_loeschen.append(alter_name)
                elif wert and wert == alter_name:
                    sauber[feld] = alter_name
                else:  # entfernt oder nie vorhanden
                    sauber[feld] = None
                    if alter_name:
                        zu_loeschen.append(alter_name)

            with self.lock:
                if spot_id:
                    self.db.aktualisieren(spot_id, sauber)
                else:
                    spot_id = self.db.einfuegen(sauber)
        except Exception:
            for name in neu_geschrieben:  # nichts Halbes zurücklassen
                (self.img_dir / name).unlink(missing_ok=True)
            raise

        for name in zu_loeschen:
            self._bild_loeschen(name)
        return self.holen(spot_id)

    def loeschen(self, spot_id):
        spot = self.holen(spot_id)
        with self.lock:
            self.db.loeschen(spot_id)
        for feld in BILD_FELDER:
            if spot[feld]:
                self._bild_loeschen(spot[feld])

    # ---------- Einstellungen der Oberfläche (z. B. Ansicht) ----------
    def einstellungen(self):
        try:
            return json.loads(self.einstellungen_datei.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def einstellungen_speichern(self, neu):
        if not isinstance(neu, dict):
            raise Fehler("Ungültige Einstellungen.")
        werte = self.einstellungen()
        werte.update({k: v for k, v in neu.items() if isinstance(v, (str, int, bool))})
        self.einstellungen_datei.write_text(json.dumps(werte, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
        return werte

    # ---------- Hilfen ----------
    def _pruefen(self, daten):
        if not isinstance(daten, dict):
            raise Fehler("Ungültige Daten.")
        sauber = {}
        for spalte in SPALTEN:
            if spalte in BILD_FELDER:
                continue
            wert = daten.get(spalte)
            if wert is None:
                sauber[spalte] = None
                continue
            if not isinstance(wert, str):
                wert = str(wert)
            wert = wert.strip()
            grenze = MAX_NOTIZEN if spalte == "notizen" else MAX_TEXT
            if len(wert) > grenze:
                raise Fehler(f"Das Feld '{spalte}' ist zu lang.")
            sauber[spalte] = wert or None

        if not sauber.get("gewaesser"):
            raise Fehler("Bitte ein Gewässer angeben.")
        if not re.fullmatch(r"\d{4}", sauber.get("port") or ""):
            raise Fehler("Der Port muss genau 4 Ziffern haben.")
        if sauber.get("datum"):
            try:
                datetime.strptime(sauber["datum"], "%Y-%m-%d")
            except ValueError:
                raise Fehler("Ungültiges Datum.")
        if sauber.get("trophaee") not in (None, *TROPHAEE_WERTE):
            raise Fehler("Ungültige Trophäen-Auswahl.")
        return sauber

    def _bild_schreiben(self, data_url):
        kopf, _, inhalt = data_url.partition(",")
        mime = kopf[5:].split(";")[0].lower()
        if mime not in BILD_TYPEN or ";base64" not in kopf:
            raise Fehler("Nur Bilder (PNG, JPG, GIF, BMP, WebP) sind erlaubt.")
        try:
            roh = base64.b64decode(inhalt, validate=True)
        except (binascii.Error, ValueError):
            raise Fehler("Bild konnte nicht gelesen werden.")
        name = f"{uuid.uuid4().hex}{BILD_TYPEN[mime]}"
        (self.img_dir / name).write_bytes(roh)
        return name

    def _bild_loeschen(self, name):
        if BILD_NAME.match(name or ""):
            (self.img_dir / name).unlink(missing_ok=True)


def handler_fuer(dienst: SpotDienst, web_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "RF4SpotDB"

        def log_message(self, *args):  # Konsole ruhig halten
            pass

        # ---------- Antworten ----------
        def _senden(self, status, inhalt: bytes, typ, cache=False):
            self.send_response(status)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(inhalt)))
            self.send_header("Cache-Control", "max-age=31536000, immutable" if cache else "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(inhalt)

        def _json(self, status, daten):
            self._senden(status, json.dumps(daten, ensure_ascii=False).encode("utf-8"),
                         "application/json; charset=utf-8")

        def _body(self):
            laenge = int(self.headers.get("Content-Length") or 0)
            if laenge > MAX_ANFRAGE:
                raise Fehler("Die Bilder sind zu groß.", 413)
            try:
                return json.loads(self.rfile.read(laenge) or b"{}")
            except ValueError:
                raise Fehler("Ungültige Anfrage.")

        def _api(self, methode):
            # Eigener Header: fremde Webseiten im Browser dürfen die API so nicht benutzen
            if self.headers.get("X-RF4") != "1":
                raise Fehler("Nicht erlaubt.", 403)
            pfad = urlparse(self.path)
            teile = [t for t in pfad.path.split("/") if t][1:]  # ohne 'api'

            if teile == ["meta"] and methode == "GET":
                return self._json(200, dienst.meta())
            if teile == ["einstellungen"]:
                if methode == "GET":
                    return self._json(200, dienst.einstellungen())
                if methode == "PUT":
                    return self._json(200, dienst.einstellungen_speichern(self._body()))
            if teile == ["spots"]:
                if methode == "GET":
                    q = {k: v[0] for k, v in parse_qs(pfad.query).items()}
                    return self._json(200, dienst.liste(q))
                if methode == "POST":
                    return self._json(201, dienst.speichern(self._body()))
            if len(teile) == 2 and teile[0] == "spots" and teile[1].isdigit():
                spot_id = int(teile[1])
                if methode == "GET":
                    return self._json(200, dienst.holen(spot_id))
                if methode == "PUT":
                    return self._json(200, dienst.speichern(self._body(), spot_id))
                if methode == "DELETE":
                    dienst.loeschen(spot_id)
                    return self._json(200, {"ok": True})
            raise Fehler("Unbekannte Anfrage.", 404)

        def _anfrage(self, methode):
            try:
                pfad = urlparse(self.path).path
                if pfad.startswith("/api/"):
                    return self._api(methode)
                if methode != "GET":
                    raise Fehler("Nicht erlaubt.", 405)
                if pfad.startswith("/bilder/"):
                    name = unquote(pfad[len("/bilder/"):])
                    datei = dienst.img_dir / name
                    if not BILD_NAME.match(name) or not datei.is_file():
                        raise Fehler("Bild nicht gefunden.", 404)
                    return self._senden(200, datei.read_bytes(),
                                        BILD_MIME[datei.suffix.lower()], cache=True)
                if pfad in STATISCH:
                    datei, typ = STATISCH[pfad]
                    return self._senden(200, (web_dir / datei).read_bytes(), typ)
                raise Fehler("Nicht gefunden.", 404)
            except ConnectionError:  # Fenster hat die Anfrage abgebrochen – egal
                return
            except Fehler as f:
                self._antwort_versuchen(f.status, str(f))
            except Exception as e:  # unerwartet: Meldung trotzdem anzeigen
                self._antwort_versuchen(500, f"Interner Fehler: {e}")

        def _antwort_versuchen(self, status, meldung):
            try:
                self._json(status, {"fehler": meldung})
            except ConnectionError:
                pass

        def do_GET(self):
            self._anfrage("GET")

        def do_POST(self):
            self._anfrage("POST")

        def do_PUT(self):
            self._anfrage("PUT")

        def do_DELETE(self):
            self._anfrage("DELETE")

    return Handler


def starte_server(data_dir: Path, web_dir: Path, gewaesser: list):
    """Startet den Server auf einem freien Port und gibt (server, url) zurück."""
    dienst = SpotDienst(data_dir, gewaesser)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_fuer(dienst, web_dir))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"
