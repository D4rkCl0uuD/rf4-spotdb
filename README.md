# RF4 Spot-Datenbank

Lokale App zum Speichern und Wiederfinden von Spots in Russian Fishing 4.
Python verwaltet im Hintergrund die SQLite-Datenbank und die Screenshots, die Oberfläche ist HTML/CSS/JavaScript und läuft in einem eigenen Fenster.
Alles läuft offline: Der kleine Server ist nur auf diesem PC erreichbar (127.0.0.1).

## Download für Windows (ohne Python)
1. Unter **[Releases](https://github.com/D4rkCl0uuD/rf4-spotdb/releases/latest)** die Datei `RF4SpotDB-Windows.zip` herunterladen.
2. ZIP entpacken (Rechtsklick → *Alle extrahieren*), z. B. auf den Desktop.
3. Im Ordner `RF4SpotDB` die **`RF4SpotDB.exe`** starten. Der erste Start dauert ein paar Sekunden.

Deine Spots werden im Ordner `daten` neben der `.exe` gespeichert. Den Ordner beim Update auf eine neue Version einfach in den neuen Ordner kopieren.

> Windows zeigt beim ersten Start evtl. „Der Computer wurde durch Windows geschützt“. Dann auf **Weitere Informationen → Trotzdem ausführen** klicken. Die App ist nicht signiert, deshalb kommt diese Meldung.
>
> Benötigt die WebView2-Laufzeit von Microsoft. Die ist bei Windows 10/11 normalerweise schon installiert.

## Aus dem Quellcode starten
- Python 3.8 oder neuer
- `pip install -r requirements.txt` (installiert pywebview für das eigene App-Fenster;
  ohne pywebview öffnet sich die App automatisch im Standard-Browser)
- Windows: Doppelklick auf `start.bat`
  (nutzt automatisch die PyCharm-Umgebung `..\.venv`, falls vorhanden)
- oder im Ordner: `python main.py`

Die alte Tkinter-Oberfläche gibt es weiterhin als `main_tkinter.py`. Sie nutzt dieselbe Datenbank.

## Dateien
- `main.py` – Start, öffnet das Fenster
- `server.py` – lokale Schnittstelle zwischen Oberfläche und Datenbank
- `db.py` – Datenbank (SQLite)
- `fischarten.py` – alle 252 Fischarten aus dem Spiel (bei Spiel-Updates hier ergänzen)
- `web/` – Oberfläche (`index.html`, `style.css`, `app.js`)

## Daten
- `daten/spots.db` – die Datenbank
- `daten/bilder/` – Kopien der Screenshots (Trophäe, Montage, Kescher)
- `daten/einstellungen.json` – z. B. ob Karten- oder Tabellenansicht

Zum Sichern einfach den ganzen Ordner `daten/` kopieren.
Ältere Datenbanken werden beim Start automatisch auf den neuen Stand gebracht. Vorher legt die App eine Sicherung `spots_backup_<Datum>_<Uhrzeit>.db` an.

## Felder
Gewässer (Pflicht, Auswahlliste + eigene Eingabe), Port (Pflicht, genau 4 Ziffern), Koordinaten, Datum (bei neuen Spots heute vorausgefüllt), Tageszeit, Fischart (Auswahl aus der Liste), Gewicht, Trophäe (Keine / Trophäe / Seltene Trophäe), Köder/Futter, Dip, Montage, Tiefe, Clip/Wurfweite, Notizen, Screenshots von Trophäe, Montage und Kescher.

## Bedienung
- **Karten / Tabelle** oben rechts umschalten. Die Wahl wird gespeichert.
- In der Tabelle sortiert ein Klick auf eine Spaltenüberschrift.
- Spot anklicken öffnet den Editor rechts.
- **Fischart**: Feld anklicken, die Liste klappt auf. Beim Tippen wird gefiltert (z. B. „spieg“ zeigt alle Spiegelkarpfen). Mit ↑/↓ und Enter wählen. Es sind nur Fischarten aus der Liste erlaubt. Ältere Einträge mit anderer Schreibweise bleiben erhalten.
- Der **Fischart-Filter** oben funktioniert genauso, das × entfernt ihn wieder.
- **Screenshots hinzufügen**: über den **+**-Knopf, durch Hineinziehen oder Feld anklicken und **Strg+V** (Screenshot direkt aus der Zwischenablage).
- **Klick auf einen Screenshot** öffnet ihn im Vollbild (Esc oder Klick schließt). Das kleine **+** am Bild ersetzt ihn, der Papierkorb entfernt ihn.
- Trophäen sind farbig wie im Spiel: Gelb = Trophäe, Blau = Seltene Trophäe.
- Tastenkürzel: **Strg+N** neuer Spot, **Strg+S** speichern, **Strg+F** suchen, **Esc** schließen.

Die Gewässerliste steht oben in `main.py` (`GEWAESSER`) und kann dort angepasst werden.
