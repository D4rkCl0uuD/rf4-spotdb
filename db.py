"""Datenbank-Schicht (SQLite) für die RF4 Spot-Datenbank."""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# Alle Spalten, die ein Spot hat (außer id und Zeitstempeln)
SPALTEN = [
    "gewaesser", "koordinaten", "port", "datum",
    "fischart", "gewicht", "trophaee",
    "koeder", "dip", "montage", "tiefe", "clip",
    "tageszeit", "notizen",
    "bild_trophaee", "bild_montage", "bild_kescher",
]

# Spalten, die in älteren Versionen fehlen und nachgerüstet werden
NEUE_SPALTEN = {"datum": "TEXT", "bild_kescher": "TEXT", "trophaee": "TEXT", "dip": "TEXT"}
# Spalten, die nicht mehr gebraucht werden
ALTE_SPALTEN = ["bewertung"]


class SpotDB:
    def __init__(self, pfad: Path):
        self.pfad = Path(pfad)
        # check_same_thread=False: der lokale Server greift aus mehreren Threads zu (mit Lock)
        self.conn = sqlite3.connect(str(self.pfad), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._tabelle_anlegen()
        self._migrieren()

    def _migrieren(self):
        """Bringt eine Datenbank aus einer älteren Version auf den aktuellen Stand."""
        vorhanden = {r["name"] for r in self.conn.execute("PRAGMA table_info(spots)")}
        hinzufuegen = [s for s in NEUE_SPALTEN if s not in vorhanden]
        entfernen = [s for s in ALTE_SPALTEN if s in vorhanden]
        if not hinzufuegen and not entfernen:
            return

        # Vor jeder Änderung eine Sicherungskopie anlegen
        self.conn.commit()
        stempel = datetime.now().strftime("%Y%m%d_%H%M%S")
        sicherung = self.pfad.with_name(f"{self.pfad.stem}_backup_{stempel}{self.pfad.suffix}")
        shutil.copy2(self.pfad, sicherung)

        for spalte in hinzufuegen:
            self.conn.execute(f"ALTER TABLE spots ADD COLUMN {spalte} {NEUE_SPALTEN[spalte]}")
        for spalte in entfernen:
            self.conn.execute(f"ALTER TABLE spots DROP COLUMN {spalte}")
        self.conn.commit()

    def _tabelle_anlegen(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                gewaesser     TEXT NOT NULL,
                koordinaten   TEXT,
                port          TEXT NOT NULL,
                datum         TEXT,
                fischart      TEXT,
                gewicht       TEXT,
                trophaee      TEXT,
                koeder        TEXT,
                dip           TEXT,
                montage       TEXT,
                tiefe         TEXT,
                clip          TEXT,
                tageszeit     TEXT,
                notizen       TEXT,
                bild_trophaee TEXT,
                bild_montage  TEXT,
                bild_kescher  TEXT,
                erstellt      TEXT DEFAULT (datetime('now','localtime')),
                geaendert     TEXT DEFAULT (datetime('now','localtime'))
            )
            """
        )
        self.conn.commit()

    # ---------- Schreiben ----------
    def einfuegen(self, daten: dict) -> int:
        werte = [daten.get(s) for s in SPALTEN]
        platzhalter = ",".join("?" for _ in SPALTEN)
        cur = self.conn.execute(
            f"INSERT INTO spots ({','.join(SPALTEN)}) VALUES ({platzhalter})", werte
        )
        self.conn.commit()
        return cur.lastrowid

    def aktualisieren(self, spot_id: int, daten: dict):
        zuweisung = ",".join(f"{s}=?" for s in SPALTEN)
        werte = [daten.get(s) for s in SPALTEN] + [spot_id]
        self.conn.execute(
            f"UPDATE spots SET {zuweisung}, geaendert=datetime('now','localtime') WHERE id=?",
            werte,
        )
        self.conn.commit()

    def loeschen(self, spot_id: int):
        self.conn.execute("DELETE FROM spots WHERE id=?", (spot_id,))
        self.conn.commit()

    # ---------- Lesen ----------
    def holen(self, spot_id: int):
        return self.conn.execute("SELECT * FROM spots WHERE id=?", (spot_id,)).fetchone()

    def suchen(self, text: str = "", gewaesser: str = "", fischart: str = "", trophaee: str = ""):
        """Filtert Spots. 'text' durchsucht alle Textfelder.
        trophaee: "" = alle, "alle_trophaeen", "keine", oder ein konkreter Wert."""
        bedingungen, parameter = [], []
        if text:
            felder = ["gewaesser", "koordinaten", "port", "fischart", "koeder", "dip",
                      "montage", "tiefe", "clip", "tageszeit", "notizen"]
            bedingungen.append("(" + " OR ".join(f"{f} LIKE ?" for f in felder) + ")")
            parameter += [f"%{text}%"] * len(felder)
        if gewaesser:
            bedingungen.append("gewaesser = ?")
            parameter.append(gewaesser)
        if fischart:  # Auswahl aus der Liste -> genaue Übereinstimmung
            bedingungen.append("fischart = ?")
            parameter.append(fischart)
        if trophaee == "alle_trophaeen":
            bedingungen.append("trophaee IS NOT NULL")
        elif trophaee == "keine":
            bedingungen.append("trophaee IS NULL")
        elif trophaee:
            bedingungen.append("trophaee = ?")
            parameter.append(trophaee)
        where = ("WHERE " + " AND ".join(bedingungen)) if bedingungen else ""
        return self.conn.execute(
            f"SELECT * FROM spots {where} ORDER BY gewaesser, datum DESC, geaendert DESC", parameter
        ).fetchall()

    def alle_fischarten(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT fischart FROM spots WHERE fischart IS NOT NULL ORDER BY fischart")]

    def alle_gewaesser(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT gewaesser FROM spots ORDER BY gewaesser")]

    def schliessen(self):
        self.conn.close()
