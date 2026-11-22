"""RF4 Spot-Datenbank – lokale Desktop-Anwendung (Tkinter + SQLite).

Alte Tkinter-Oberfläche (Ersatz). Start: python main_tkinter.py
Daten:  Ordner 'daten' neben dieser Datei (spots.db + bilder/)
"""
import os
import re
import shutil
import subprocess
import sys
import tkinter as tk
import uuid
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from db import SpotDB
from fischarten import FISCHARTEN


def de_sortierung(text):
    """Sortiert Umlaute wie im Deutschen (Ä bei A usw.)."""
    return (text.casefold().replace("ä", "a").replace("ö", "o")
            .replace("ü", "u").replace("ß", "ss"))


FISCHARTEN_SORTIERT = sorted(FISCHARTEN, key=de_sortierung)

try:  # Pillow ist optional – damit gehen auch JPG/WebP-Vorschauen
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "daten"
IMG_DIR = DATA_DIR / "bilder"
DB_PATH = DATA_DIR / "spots.db"

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

# Einfache Textfelder im Formular: (Schlüssel, Beschriftung)
TEXTFELDER = [
    ("datum", "Datum (TT.MM.JJJJ)"),
    ("tageszeit", "Tageszeit (Ingame)"),
    ("koordinaten", "Koordinaten"),
    ("fischart", "Fischart"),
    ("gewicht", "Gewicht"),
    ("trophaee", "Trophäe"),
    ("koeder", "Köder / Futter"),
    ("dip", "Dip"),
    ("montage", "Montage"),
    ("tiefe", "Tiefe"),
    ("clip", "Clip / Wurfweite"),
]

VORSCHAU = (180, 120)

# Trophäen-Auswahl (None = keine Trophäe) und Farben aus dem Spiel
TROPHAEE_KEINE = "Keine"
TROPHAEE_WERTE = [TROPHAEE_KEINE, "Trophäe", "Seltene Trophäe"]
TROPHAEE_FARBEN = {
    "Trophäe": "#FCC400",          # Gelb wie im RF4-Fangfenster
    "Seltene Trophäe": "#79C0FF",  # Blau wie im RF4-Fangfenster
}
# Filter-Auswahl -> Wert für db.suchen()
TROPHAEE_FILTER = {
    "Alle": "",
    "Nur Trophäen (beide)": "alle_trophaeen",
    "Trophäe": "Trophäe",
    "Seltene Trophäe": "Seltene Trophäe",
    "Keine Trophäe": "keine",
}


def datum_anzeige(iso):
    """'2026-11-20' -> '20.11.2026'"""
    if not iso:
        return ""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso


def datum_speichern(text):
    """'20.11.2026' -> '2026-11-20' (für richtige Sortierung). None bei leer, ValueError bei ungültig."""
    if not text:
        return None
    return datetime.strptime(text, "%d.%m.%Y").strftime("%Y-%m-%d")
BILD_TYPEN = [("Bilder", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("Alle Dateien", "*.*")]


def datei_oeffnen(pfad: Path):
    """Öffnet eine Datei mit dem Standardprogramm des Systems."""
    if sys.platform.startswith("win"):
        os.startfile(str(pfad))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(pfad)])
    else:
        subprocess.Popen(["xdg-open", str(pfad)])


class BildFeld(ttk.LabelFrame):
    """Ein Screenshot-Feld mit Vorschau. Bilder werden erst beim Speichern kopiert."""

    def __init__(self, master, titel: str):
        super().__init__(master, text=titel, padding=6)
        self.gespeichert = None   # Dateiname in IMG_DIR
        self.neue_quelle = None   # ausgewählte Datei, noch nicht kopiert
        self.entfernen = False
        self._foto = None

        self.vorschau = ttk.Label(self, text="Kein Bild", anchor="center",
                                  cursor="hand2")
        self.vorschau.pack(fill="both", expand=True, ipady=30)
        self.vorschau.bind("<Button-1>", lambda e: self.oeffnen())

        knoepfe = ttk.Frame(self)
        knoepfe.pack(fill="x", pady=(6, 0))
        ttk.Button(knoepfe, text="Wählen …", command=self.waehlen).pack(
            side="left", fill="x", expand=True)
        ttk.Button(knoepfe, text="Entfernen", command=self.leeren).pack(
            side="left", fill="x", expand=True, padx=(4, 0))

    def setzen(self, dateiname):
        self.gespeichert = dateiname or None
        self.neue_quelle = None
        self.entfernen = False
        self._anzeigen(IMG_DIR / dateiname if dateiname else None)

    def aktueller_pfad(self):
        if self.neue_quelle:
            return self.neue_quelle
        if self.gespeichert and not self.entfernen:
            return IMG_DIR / self.gespeichert
        return None

    def waehlen(self):
        pfad = filedialog.askopenfilename(title="Screenshot wählen", filetypes=BILD_TYPEN)
        if pfad:
            self.neue_quelle = Path(pfad)
            self._anzeigen(self.neue_quelle)

    def leeren(self):
        self.neue_quelle = None
        self.entfernen = True
        self._anzeigen(None)

    def uebernehmen(self):
        """Kopiert ein neu gewähltes Bild in den App-Ordner.
        Gibt (Dateiname für DB, alte Datei zum Löschen oder None) zurück."""
        alt = self.gespeichert
        if self.neue_quelle:
            ziel = f"{uuid.uuid4().hex}{self.neue_quelle.suffix.lower()}"
            shutil.copy2(self.neue_quelle, IMG_DIR / ziel)
            return ziel, alt
        if self.entfernen:
            return None, alt
        return alt, None

    def _anzeigen(self, pfad):
        self._foto = None
        if pfad is None:
            self.vorschau.configure(image="", text="Kein Bild")
            return
        if not Path(pfad).exists():
            self.vorschau.configure(image="", text="Bilddatei nicht gefunden")
            return
        try:
            if PIL_OK:
                bild = Image.open(pfad)
                bild.thumbnail(VORSCHAU)
                self._foto = ImageTk.PhotoImage(bild)
            else:  # ohne Pillow: nur PNG/GIF
                foto = tk.PhotoImage(file=str(pfad))
                faktor = max(1, -(-foto.width() // VORSCHAU[0]), -(-foto.height() // VORSCHAU[1]))
                self._foto = foto.subsample(faktor, faktor)
            self.vorschau.configure(image=self._foto, text="")
        except Exception:
            hinweis = "" if PIL_OK else "\n(Tipp: pip install pillow)"
            self.vorschau.configure(image="", text=f"Keine Vorschau möglich{hinweis}\nKlicken zum Öffnen")

    def oeffnen(self):
        pfad = self.aktueller_pfad()
        if pfad and Path(pfad).exists():
            datei_oeffnen(pfad)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RF4 Spot-Datenbank")
        self.geometry("1500x850")  # Größe, wenn man das Fenster wiederherstellt
        self._maximieren()
        self.minsize(1050, 650)

        IMG_DIR.mkdir(parents=True, exist_ok=True)
        self.db = SpotDB(DB_PATH)
        self.aktuelle_id = None

        self._oberflaeche()
        self.liste_laden()
        self.neu()
        self.protocol("WM_DELETE_WINDOW", self._beenden)

    def _maximieren(self):
        """Startet das Fenster maximiert (Titel- und Taskleiste bleiben sichtbar)."""
        try:
            self.state("zoomed")  # Windows / macOS
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                pass

    # ---------------- Aufbau ----------------
    def _oberflaeche(self):
        stil = ttk.Style(self)
        if "clam" in stil.theme_names():
            stil.theme_use("clam")
        stil.configure("Treeview", rowheight=24)

        teiler = ttk.PanedWindow(self, orient="horizontal")
        teiler.pack(fill="both", expand=True, padx=8, pady=8)

        links = ttk.Frame(teiler, padding=4)
        rechts = ttk.Frame(teiler, padding=4)
        teiler.add(links, weight=3)
        teiler.add(rechts, weight=2)

        self._filterleiste(links)
        self._liste(links)
        self._formular(rechts)

    def _filterleiste(self, master):
        leiste = ttk.LabelFrame(master, text="Suche & Filter", padding=6)
        leiste.pack(fill="x")

        self.f_text = tk.StringVar()
        self.f_gew = tk.StringVar(value="Alle")
        self.f_fisch = tk.StringVar(value="Alle")
        self.f_troph = tk.StringVar(value="Alle")

        leiste.columnconfigure(1, weight=1)
        leiste.columnconfigure(3, weight=1)
        ttk.Label(leiste, text="Suche:").grid(row=0, column=0, sticky="w")
        ttk.Entry(leiste, textvariable=self.f_text).grid(
            row=0, column=1, columnspan=3, sticky="ew", padx=(4, 10), pady=(0, 4))
        ttk.Button(leiste, text="Zurücksetzen", command=self._filter_zuruecksetzen).grid(
            row=0, column=4, sticky="ew", pady=(0, 4))
        ttk.Label(leiste, text="Gewässer:").grid(row=1, column=0, sticky="w")
        self.f_gew_box = ttk.Combobox(leiste, textvariable=self.f_gew, state="readonly")
        self.f_gew_box.grid(row=1, column=1, sticky="ew", padx=(4, 10))
        ttk.Label(leiste, text="Fischart:").grid(row=1, column=2, sticky="w")
        self.f_fisch_box = ttk.Combobox(leiste, textvariable=self.f_fisch, state="readonly", height=20)
        self.f_fisch_box.grid(row=1, column=3, columnspan=2, sticky="ew", padx=(4, 0))
        ttk.Label(leiste, text="Trophäe:").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Combobox(leiste, textvariable=self.f_troph, state="readonly",
                     values=list(TROPHAEE_FILTER)).grid(
            row=2, column=1, sticky="ew", padx=(4, 10), pady=(4, 0))

        for var in (self.f_text, self.f_gew, self.f_fisch, self.f_troph):
            var.trace_add("write", lambda *_: self.liste_laden())

    def _liste(self, master):
        rahmen = ttk.Frame(master)
        rahmen.pack(fill="both", expand=True, pady=(8, 0))

        spalten = [("gewaesser", "Gewässer", 120), ("datum", "Datum", 90),
                   ("koordinaten", "Koord.", 60), ("port", "Port", 45),
                   ("fischart", "Fischart", 110), ("gewicht", "Gewicht", 65),
                   ("trophaee", "Trophäe", 120), ("koeder", "Köder", 100),
                   ("tiefe", "Tiefe", 50)]
        self.baum = ttk.Treeview(rahmen, columns=[s[0] for s in spalten],
                                 show="headings", selectmode="browse")
        for schluessel, titel, breite in spalten:
            self.baum.heading(schluessel, text=titel)
            # Spalten wachsen mit dem Fenster, schrumpfen aber nicht unter 'breite'
            self.baum.column(schluessel, width=breite, minwidth=breite, stretch=True, anchor="w")
        scroll = ttk.Scrollbar(rahmen, orient="vertical", command=self.baum.yview)
        scroll_x = ttk.Scrollbar(rahmen, orient="horizontal", command=self.baum.xview)
        self.baum.configure(yscrollcommand=scroll.set, xscrollcommand=scroll_x.set)
        rahmen.rowconfigure(0, weight=1)
        rahmen.columnconfigure(0, weight=1)
        self.baum.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        self.baum.bind("<<TreeviewSelect>>", self._auswahl)
        for wert, farbe in TROPHAEE_FARBEN.items():
            self.baum.tag_configure(wert, background=farbe, foreground="#1A1A1A")

        self.status = ttk.Label(master, text="", foreground="#555")
        self.status.pack(fill="x", pady=(4, 0))

    def _formular(self, master):
        kopf = ttk.Frame(master)
        kopf.pack(fill="x")
        self.titel = ttk.Label(kopf, text="Neuer Spot", font=("Segoe UI", 13, "bold"))
        self.titel.pack(side="left")

        felder = ttk.Frame(master)
        felder.pack(fill="x", pady=(8, 0))
        felder.columnconfigure(1, weight=1)
        felder.columnconfigure(3, weight=1)

        self.vars = {}

        # Pflichtfelder
        self.vars["gewaesser"] = tk.StringVar()
        ttk.Label(felder, text="Gewässer *").grid(row=0, column=0, sticky="w", pady=2)
        self.gew_box = ttk.Combobox(felder, textvariable=self.vars["gewaesser"], values=GEWAESSER)
        self.gew_box.grid(row=0, column=1, sticky="ew", padx=(4, 12), pady=2)

        self.vars["port"] = tk.StringVar()
        nur_ziffern = (self.register(lambda s: s == "" or (s.isdigit() and len(s) <= 4)), "%P")
        ttk.Label(felder, text="Port *").grid(row=0, column=2, sticky="w", pady=2)
        ttk.Entry(felder, textvariable=self.vars["port"], width=8,
                  validate="key", validatecommand=nur_ziffern).grid(row=0, column=3, sticky="w", padx=4, pady=2)

        # Weitere Felder zweispaltig
        for i, (schluessel, beschriftung) in enumerate(TEXTFELDER):
            zeile, spalte = 1 + i // 2, (i % 2) * 2
            self.vars[schluessel] = tk.StringVar()
            ttk.Label(felder, text=beschriftung).grid(row=zeile, column=spalte, sticky="w", pady=2)
            if schluessel == "trophaee":
                eingabe = ttk.Combobox(felder, textvariable=self.vars[schluessel],
                                       values=TROPHAEE_WERTE, state="readonly")
            elif schluessel == "fischart":  # nur Fischarten aus der Liste
                eingabe = ttk.Combobox(felder, textvariable=self.vars[schluessel],
                                       values=[""] + FISCHARTEN_SORTIERT, state="readonly", height=20)
            else:
                eingabe = ttk.Entry(felder, textvariable=self.vars[schluessel])
            eingabe.grid(
                row=zeile, column=spalte + 1, sticky="ew", padx=(4, 12 if spalte == 0 else 4), pady=2)

        ttk.Label(master, text="Notizen").pack(anchor="w", pady=(8, 2))
        self.notizen = tk.Text(master, height=5, wrap="word", font=("Segoe UI", 10))
        self.notizen.pack(fill="x")

        bilder = ttk.Frame(master)
        bilder.pack(fill="both", expand=True, pady=(8, 0))
        self.bild_trophaee = BildFeld(bilder, "Screenshot Trophäe")
        self.bild_montage = BildFeld(bilder, "Screenshot Montage")
        self.bild_kescher = BildFeld(bilder, "Screenshot Kescher")
        bilder.rowconfigure(0, weight=1)
        for spalte, (feld, abstand) in enumerate(((self.bild_trophaee, (0, 4)),
                                                   (self.bild_montage, 4),
                                                   (self.bild_kescher, (4, 0)))):
            bilder.columnconfigure(spalte, weight=1, uniform="bilder")
            feld.grid(row=0, column=spalte, sticky="nsew", padx=abstand)
        self.bildfelder = {"bild_trophaee": self.bild_trophaee,
                           "bild_montage": self.bild_montage,
                           "bild_kescher": self.bild_kescher}

        knoepfe = ttk.Frame(master)
        knoepfe.pack(fill="x", pady=(10, 0))
        ttk.Button(knoepfe, text="Neu", command=self.neu).pack(side="left")
        ttk.Button(knoepfe, text="Speichern", command=self.speichern).pack(side="left", padx=6)
        self.loeschen_knopf = ttk.Button(knoepfe, text="Löschen", command=self.loeschen)
        self.loeschen_knopf.pack(side="right")

        self.bind("<Control-s>", lambda e: self.speichern())
        self.bind("<Control-n>", lambda e: self.neu())

    # ---------------- Liste ----------------
    def _gewaesser_filter_aktualisieren(self):
        werte = sorted(set(GEWAESSER) | set(self.db.alle_gewaesser()))
        self.f_gew_box.configure(values=["Alle"] + werte)
        alte = [f for f in self.db.alle_fischarten() if f not in FISCHARTEN]
        self.f_fisch_box.configure(values=["Alle"] + sorted(FISCHARTEN + alte, key=de_sortierung))

    def liste_laden(self, markieren=None):
        self._gewaesser_filter_aktualisieren()
        gew = self.f_gew.get()
        zeilen = self.db.suchen(self.f_text.get().strip(),
                                "" if gew in ("", "Alle") else gew,
                                "" if self.f_fisch.get() in ("", "Alle") else self.f_fisch.get(),
                                TROPHAEE_FILTER.get(self.f_troph.get(), ""))
        self.baum.delete(*self.baum.get_children())
        for z in zeilen:
            self.baum.insert("", "end", iid=str(z["id"]), tags=(z["trophaee"] or "",), values=(
                z["gewaesser"], datum_anzeige(z["datum"]), z["koordinaten"] or "", z["port"],
                z["fischart"] or "", z["gewicht"] or "", z["trophaee"] or "",
                z["koeder"] or "", z["tiefe"] or ""))
        self.status.configure(text=f"{len(zeilen)} Spot(s) angezeigt")
        if markieren and self.baum.exists(str(markieren)):
            self.baum.selection_set(str(markieren))
            self.baum.see(str(markieren))

    def _filter_zuruecksetzen(self):
        self.f_text.set("")
        self.f_fisch.set("Alle")
        self.f_gew.set("Alle")
        self.f_troph.set("Alle")

    def _auswahl(self, _event=None):
        auswahl = self.baum.selection()
        if auswahl:
            self._spot_laden(int(auswahl[0]))

    # ---------------- Formular ----------------
    def _spot_laden(self, spot_id):
        spot = self.db.holen(spot_id)
        if not spot:
            return
        self.aktuelle_id = spot_id
        for schluessel, var in self.vars.items():
            wert = spot[schluessel]
            var.set("" if wert is None else str(wert))
        self.vars["datum"].set(datum_anzeige(spot["datum"]))
        self.vars["trophaee"].set(spot["trophaee"] or TROPHAEE_KEINE)
        self.notizen.delete("1.0", "end")
        self.notizen.insert("1.0", spot["notizen"] or "")
        for schluessel, feld in self.bildfelder.items():
            feld.setzen(spot[schluessel])
        self.titel.configure(text=f"Spot #{spot_id} bearbeiten")
        self.loeschen_knopf.state(["!disabled"])

    def neu(self):
        self.aktuelle_id = None
        for var in self.vars.values():
            var.set("")
        self.vars["datum"].set(date.today().strftime("%d.%m.%Y"))
        self.vars["trophaee"].set(TROPHAEE_KEINE)
        self.notizen.delete("1.0", "end")
        for feld in self.bildfelder.values():
            feld.setzen(None)
        self.titel.configure(text="Neuer Spot")
        self.loeschen_knopf.state(["disabled"])
        self.baum.selection_remove(self.baum.selection())

    def speichern(self):
        daten = {k: v.get().strip() for k, v in self.vars.items()}
        daten["notizen"] = self.notizen.get("1.0", "end").strip()

        if not daten["gewaesser"]:
            messagebox.showwarning("Fehlende Angabe", "Bitte ein Gewässer auswählen.")
            return
        if not re.fullmatch(r"\d{4}", daten["port"]):
            messagebox.showwarning("Ungültiger Port", "Der Port muss genau 4 Ziffern haben.")
            return
        bisher = self.db.holen(self.aktuelle_id)["fischart"] if self.aktuelle_id else None
        if daten["fischart"] and daten["fischart"] not in FISCHARTEN and daten["fischart"] != bisher:
            messagebox.showwarning("Unbekannte Fischart", "Bitte eine Fischart aus der Liste wählen.")
            return
        try:
            daten["datum"] = datum_speichern(daten["datum"])
        except ValueError:
            messagebox.showwarning("Ungültiges Datum",
                                   "Bitte das Datum im Format TT.MM.JJJJ eingeben, z. B. 20.11.2026.")
            return
        if daten["trophaee"] == TROPHAEE_KEINE:
            daten["trophaee"] = None
        for k in daten:
            if daten[k] == "":
                daten[k] = None

        alte_bilder = []
        try:
            for schluessel, feld in self.bildfelder.items():
                daten[schluessel], alt = feld.uebernehmen()
                alte_bilder.append(alt)
        except OSError as fehler:
            messagebox.showerror("Bild konnte nicht kopiert werden", str(fehler))
            return

        if self.aktuelle_id:
            self.db.aktualisieren(self.aktuelle_id, daten)
            spot_id = self.aktuelle_id
        else:
            spot_id = self.db.einfuegen(daten)

        for alt in alte_bilder:  # ersetzte/entfernte Bilder aufräumen
            if alt:
                (IMG_DIR / alt).unlink(missing_ok=True)

        self.liste_laden(markieren=spot_id)
        self._spot_laden(spot_id)
        self.status.configure(text=f"Spot #{spot_id} gespeichert")

    def loeschen(self):
        if not self.aktuelle_id:
            return
        if not messagebox.askyesno("Spot löschen", f"Spot #{self.aktuelle_id} wirklich löschen?"):
            return
        spot = self.db.holen(self.aktuelle_id)
        for bild in (spot["bild_trophaee"], spot["bild_montage"], spot["bild_kescher"]):
            if bild:
                (IMG_DIR / bild).unlink(missing_ok=True)
        self.db.loeschen(self.aktuelle_id)
        self.neu()
        self.liste_laden()

    def _beenden(self):
        self.db.schliessen()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
