/* RF4 Spot-Datenbank – Oberfläche (reines JavaScript, keine Abhängigkeiten) */
"use strict";

const BILD_FELDER = ["bild_trophaee", "bild_montage", "bild_kescher"];
const TEXT_FELDER = ["gewaesser", "port", "koordinaten", "datum", "tageszeit", "fischart",
                     "gewicht", "koeder", "dip", "montage", "tiefe", "clip", "notizen"];
const MAX_BILD_MB = 40;

const ICON = {
  stern: '<svg viewBox="0 0 24 24"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
  krone: '<svg viewBox="0 0 24 24"><path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 10H5z"/></svg>',
  fisch: '<svg class="platzhalter" viewBox="0 0 24 24"><path d="M2 12c3-4.5 7.5-6.5 12-6.5 3 0 5.5 1.5 7 4-1.5 2.5-4 4-7 4-1.5 0-3-.3-4.5-.8L7 17l-.6-4.4C4.7 12.3 3.3 11.7 2 12z"/><circle cx="17" cy="9.5" r=".6"/></svg>',
  ort: '<svg viewBox="0 0 24 24"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
  kreuz: '<svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/></svg>',
  server: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>',
  bild: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5L5 20"/></svg>',
  hochladen: '<svg viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>',
  muell: '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>',
  plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  leer: '<svg viewBox="0 0 24 24"><path d="M2 12c3-4.5 7.5-6.5 12-6.5 3 0 5.5 1.5 7 4-1.5 2.5-4 4-7 4-1.5 0-3-.3-4.5-.8L7 17l-.6-4.4C4.7 12.3 3.3 11.7 2 12z"/><path d="M17 9.5h.01"/></svg>',
};

const zustand = {
  spots: [],
  meta: { gewaesser: [], trophaeen: [] },
  filter: { text: "", gewaesser: "", fischart: "", trophaee: "" },
  ansicht: "karten",
  sortierung: { feld: "datum", richtung: -1 },
  editor: null, // { id, bilder: {feld: {name, neu}}, trophaee, geaendert, aktivesBild }
};

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

/* ---------------- Hilfen ---------------- */
function esc(wert) {
  return String(wert ?? "").replace(/[&<>"']/g, (z) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[z]));
}

function datumDE(iso) {
  if (!iso) return "";
  const [j, m, t] = iso.split("-");
  return t ? `${t}.${m}.${j}` : iso;
}

function zeitDE(sqlZeit) {
  // '2026-11-20 21:06:14' -> '20.11.2026, 21:06'
  if (!sqlZeit) return "";
  const [d, z = ""] = sqlZeit.split(" ");
  return `${datumDE(d)}${z ? ", " + z.slice(0, 5) : ""}`;
}

function heuteISO() {
  const d = new Date();
  const zwei = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${zwei(d.getMonth() + 1)}-${zwei(d.getDate())}`;
}

function trophaeenKlasse(t) {
  return t === "Seltene Trophäe" ? "blau" : t === "Trophäe" ? "gelb" : "";
}

function abzeichen(t) {
  const k = trophaeenKlasse(t);
  if (!k) return "";
  return `<span class="abzeichen ${k}">${k === "blau" ? ICON.krone : ICON.stern}${esc(t)}</span>`;
}

function bildURL(name) {
  return name ? `/bilder/${encodeURIComponent(name)}` : "";
}

async function api(methode, pfad, daten) {
  const optionen = { method: methode, headers: { "X-RF4": "1" } };
  if (daten !== undefined) {
    optionen.headers["Content-Type"] = "application/json";
    optionen.body = JSON.stringify(daten);
  }
  let antwort;
  try {
    antwort = await fetch(`/api/${pfad}`, optionen);
  } catch {
    throw new Error("Keine Verbindung zur App. Läuft das Programm noch?");
  }
  const json = await antwort.json().catch(() => ({}));
  if (!antwort.ok) throw new Error(json.fehler || `Fehler ${antwort.status}`);
  return json;
}

function toast(text, art = "") {
  const el = document.createElement("div");
  el.className = `toast ${art}`;
  el.textContent = text;
  $("#toasts").append(el);
  setTimeout(() => { el.classList.add("weg"); setTimeout(() => el.remove(), 300); }, art === "fehler" ? 4500 : 2200);
}

function bestaetigen(titel, text, knopf = "OK") {
  return new Promise((fertig) => {
    const huelle = $("#dialog");
    $(".dialog-titel", huelle).textContent = titel;
    $(".dialog-text", huelle).textContent = text;
    $('[data-antwort="ja"]', huelle).textContent = knopf;
    huelle.hidden = false;
    $('[data-antwort="ja"]', huelle).focus();
    const ende = (wert) => {
      huelle.hidden = true;
      huelle.removeEventListener("click", klick);
      document.removeEventListener("keydown", taste, true);
      fertig(wert);
    };
    const klick = (e) => {
      if (e.target === huelle) return ende(false);
      const a = e.target.closest("[data-antwort]");
      if (a) ende(a.dataset.antwort === "ja");
    };
    const taste = (e) => {
      if (e.key === "Escape") { e.stopPropagation(); ende(false); }
    };
    huelle.addEventListener("click", klick);
    document.addEventListener("keydown", taste, true);
  });
}

function entprellen(fn, ms = 200) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/* ---------------- Suchbares Dropdown (z. B. Fischart) ---------------- */
const kollator = new Intl.Collator("de", { sensitivity: "base", numeric: true });

// Für den Vergleich: Groß/Klein, Akzente, ß, Bindestriche und Leerzeichen egal
function normal(text) {
  return String(text ?? "").toLocaleLowerCase("de").replace(/ß/g, "ss")
    .normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[\s\-.()]+/g, "");
}

function markieren(name, suche) {
  const i = suche ? name.toLocaleLowerCase("de").indexOf(suche.toLocaleLowerCase("de")) : -1;
  if (i < 0) return esc(name);
  return esc(name.slice(0, i)) + "<mark>" + esc(name.slice(i, i + suche.length)) + "</mark>" + esc(name.slice(i + suche.length));
}

/**
 * Macht aus .auswahl (Eingabefeld + Liste) ein suchbares Dropdown.
 * optionen(): [{wert, hinweis?}]  – nur diese Werte sind erlaubt
 * leerOption: Text für "nichts gewählt" (z. B. "Alle Fischarten") oder null
 */
function auswahlFeld(huelle, { optionen, beiWahl, leerOption = null, meldungUnbekannt }) {
  const input = $("input", huelle);
  const liste = $(".auswahl-liste", huelle);
  const leeren = $(".auswahl-leeren", huelle);
  let wert = "";       // aktuell festgelegter Wert
  let getippt = false; // nur filtern, wenn der Nutzer etwas getippt hat
  let treffer = [];
  let aktiv = -1;

  function suchen() {
    const roh = getippt ? input.value.trim() : "";
    const q = normal(roh);
    let liste_ = optionen().map((o) => ({ ...o, n: normal(o.wert) }));
    if (q) {
      const wort = roh.toLocaleLowerCase("de");
      liste_ = liste_
        .map((o) => {
          const klein = o.wert.toLocaleLowerCase("de");
          const rang = o.n.startsWith(q) ? 0
            : klein.split(/[\s\-]+/).some((w) => w.startsWith(wort)) ? 1
            : o.n.includes(q) ? 2 : 9;
          return { ...o, rang };
        })
        .filter((o) => o.rang < 9)
        .sort((a, b) => a.rang - b.rang || kollator.compare(a.wert, b.wert));
    } else {
      liste_.sort((a, b) => kollator.compare(a.wert, b.wert));
      if (leerOption) liste_.unshift({ wert: "", text: leerOption });
    }
    return { liste: liste_, roh };
  }

  function zeichnen() {
    const { liste: l, roh } = suchen();
    treffer = l;
    if (!treffer.length) {
      liste.innerHTML = `<div class="auswahl-leer">Keine Fischart gefunden für „${esc(roh)}“</div>`;
      aktiv = -1;
      return;
    }
    if (aktiv < 0 || aktiv >= treffer.length) {
      aktiv = getippt ? 0 : Math.max(0, treffer.findIndex((o) => o.wert === wert));
    }
    liste.innerHTML = treffer.map((o, i) => `
      <div class="auswahl-option${i === aktiv ? " aktiv" : ""}${o.wert === wert ? " gewaehlt" : ""}${o.wert === "" ? " leer-option" : ""}"
           role="option" data-index="${i}">
        <span>${o.text ? esc(o.text) : markieren(o.wert, getippt ? roh : "")}</span>
        ${o.hinweis ? `<small>${esc(o.hinweis)}</small>` : ""}
      </div>`).join("");
    $(".auswahl-option.aktiv", liste)?.scrollIntoView({ block: "nearest" });
  }

  function oeffnen() {
    if (!liste.hidden) return;
    getippt = false;
    aktiv = -1;
    zeichnen();
    liste.hidden = false;
    huelle.classList.add("offen");
    input.setAttribute("aria-expanded", "true");
    input.select();
  }

  function schliessen() {
    liste.hidden = true;
    huelle.classList.remove("offen");
    input.setAttribute("aria-expanded", "false");
  }

  function anzeigen() {
    input.value = wert;
    if (leeren) leeren.hidden = !wert;
    huelle.classList.toggle("hat-wert", Boolean(wert));
  }

  function waehlen(neu, melden = true) {
    const alt = wert;
    wert = neu;
    anzeigen();
    schliessen();
    if (melden && neu !== alt) beiWahl(neu);
  }

  // Getippten Text übernehmen, wenn er (bis auf Schreibweise) einer Option entspricht
  function festschreiben(still = false) {
    const roh = input.value.trim();
    if (!roh) { if (wert) waehlen(""); else anzeigen(); return true; }
    if (roh === wert) { anzeigen(); return true; }
    const passend = optionen().find((o) => normal(o.wert) === normal(roh));
    if (passend) { waehlen(passend.wert); return true; }
    anzeigen(); // zurück zum letzten gültigen Wert
    if (meldungUnbekannt && !still) toast(meldungUnbekannt, "fehler");
    return false;
  }

  input.addEventListener("focus", oeffnen);
  input.addEventListener("click", oeffnen);
  input.addEventListener("input", () => {
    getippt = true;
    aktiv = -1;
    if (liste.hidden) { liste.hidden = false; huelle.classList.add("offen"); }
    zeichnen();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (liste.hidden) return oeffnen();
      if (!treffer.length) return;
      aktiv = (aktiv + (e.key === "ArrowDown" ? 1 : -1) + treffer.length) % treffer.length;
      zeichnen();
    } else if (e.key === "Enter") {
      if (!liste.hidden) {
        e.preventDefault();
        if (treffer[aktiv]) waehlen(treffer[aktiv].wert); else festschreiben();
      }
    } else if (e.key === "Escape" && !liste.hidden) {
      e.stopPropagation();
      anzeigen();
      schliessen();
    } else if (e.key === "Tab" && !liste.hidden) {
      if (getippt && treffer[aktiv]) waehlen(treffer[aktiv].wert); else festschreiben();
    }
  });
  huelle.addEventListener("focusout", (e) => {
    if (huelle.contains(e.relatedTarget)) return;
    if (!liste.hidden) { festschreiben(); schliessen(); }
  });
  liste.addEventListener("mousedown", (e) => e.preventDefault()); // Fokus im Feld lassen
  liste.addEventListener("click", (e) => {
    const o = e.target.closest(".auswahl-option");
    if (o) waehlen(treffer[Number(o.dataset.index)].wert);
  });
  leeren?.addEventListener("click", () => waehlen(""));

  return {
    setzen(neu) { wert = neu || ""; anzeigen(); schliessen(); },
    get wert() { return wert; },
    festschreiben,
  };
}

let fischEditor = null;
let fischFilter = null;

function fischOptionen(mitAlten) {
  const liste = (zustand.meta.fischarten || []).map((w) => ({ wert: w }));
  const alte = mitAlten === "filter"
    ? (zustand.meta.fischarten_alt || [])
    : (zustand.editor?.fischAlt && !(zustand.meta.fischarten || []).includes(zustand.editor.fischAlt) ? [zustand.editor.fischAlt] : []);
  return liste.concat(alte.map((w) => ({ wert: w, hinweis: "alte Schreibweise" })));
}

/* ---------------- Laden & Anzeigen ---------------- */
async function metaLaden() {
  zustand.meta = await api("GET", "meta");
  const auswahl = $("#f-gewaesser");
  const aktuell = zustand.filter.gewaesser;
  auswahl.innerHTML = `<option value="">Alle Gewässer</option>` +
    zustand.meta.gewaesser.map((g) => `<option value="${esc(g)}">${esc(g)}</option>`).join("");
  auswahl.value = aktuell;
  $("#gewaesser-liste").innerHTML = zustand.meta.gewaesser.map((g) => `<option value="${esc(g)}">`).join("");
}

async function spotsLaden() {
  const q = new URLSearchParams(Object.entries(zustand.filter).filter(([, v]) => v));
  try {
    zustand.spots = await api("GET", `spots?${q}`);
  } catch (e) {
    toast(e.message, "fehler");
    zustand.spots = [];
  }
  zeichnen();
}

function sortiert(spots) {
  const { feld, richtung } = zustand.sortierung;
  const wert = (s) => {
    const v = s[feld];
    if (feld === "gewicht") return parseFloat(String(v ?? "").replace(",", ".")) || -Infinity;
    if (feld === "trophaee") return v === "Seltene Trophäe" ? 2 : v === "Trophäe" ? 1 : 0;
    return (v ?? "").toString().toLowerCase();
  };
  return [...spots].sort((a, b) => {
    const x = wert(a), y = wert(b);
    if (x < y) return -richtung;
    if (x > y) return richtung;
    return b.id - a.id;
  });
}

function zeichnen() {
  const inhalt = $("#inhalt");
  const filterAktiv = Object.values(zustand.filter).some(Boolean);
  $("#anzahl").textContent = `${zustand.spots.length} Spot${zustand.spots.length === 1 ? "" : "s"}`;
  $("#f-reset").hidden = !filterAktiv;

  if (!zustand.spots.length) {
    inhalt.innerHTML = filterAktiv
      ? `<div class="leer"><div>${ICON.leer}<h2>Keine Treffer</h2><p>Für diese Filter gibt es keine Spots.</p>
           <button class="btn btn-sekundaer" data-aktion="reset">Filter zurücksetzen</button></div></div>`
      : `<div class="leer"><div>${ICON.leer}<h2>Noch keine Spots</h2><p>Lege deinen ersten Spot an.</p>
           <button class="btn btn-primaer" data-aktion="neu">Neuer Spot</button></div></div>`;
    return;
  }
  const spots = sortiert(zustand.spots);
  inhalt.innerHTML = zustand.ansicht === "tabelle" ? tabelleHTML(spots) : kartenHTML(spots);
}

function kartenHTML(spots) {
  return `<div class="karten">${spots.map((s) => {
    const k = trophaeenKlasse(s.trophaee);
    const titelbild = s.bild_trophaee || s.bild_kescher || s.bild_montage;
    const anzahlBilder = BILD_FELDER.filter((f) => s[f]).length;
    const details = [["Köder", s.koeder], ["Dip", s.dip], ["Montage", s.montage], ["Tiefe", s.tiefe], ["Clip", s.clip]]
      .filter(([, v]) => v)
      .slice(0, 3)
      .map(([n, v]) => `<div><b>${n}</b>${esc(v)}</div>`).join("");
    return `
      <article class="karte ${k ? "t-" + k : ""}" data-id="${s.id}" tabindex="0">
        <div class="karte-bild">
          ${titelbild ? `<img src="${bildURL(titelbild)}" alt="" loading="lazy">` : ICON.fisch}
          ${abzeichen(s.trophaee)}
          ${anzahlBilder ? `<span class="bild-anzahl">${ICON.bild}${anzahlBilder}</span>` : ""}
        </div>
        <div class="karte-text">
          <div class="karte-zeile1">
            <div class="karte-fisch" title="${esc(s.fischart)}">${esc(s.fischart || "Unbekannter Fisch")}</div>
            ${s.gewicht ? `<div class="karte-gewicht">${esc(s.gewicht)}</div>` : ""}
          </div>
          <div class="karte-ort">
            <span class="tag">${ICON.ort}${esc(s.gewaesser)}</span>
            ${s.koordinaten ? `<span class="tag mono">${ICON.kreuz}${esc(s.koordinaten)}</span>` : ""}
            <span class="tag mono" title="Port">${ICON.server}${esc(s.port)}</span>
          </div>
          ${details ? `<div class="karte-details">${details}</div>` : ""}
          <div class="karte-fuss">
            <span>${esc(datumDE(s.datum)) || "ohne Datum"}</span>
            <span>${esc(s.tageszeit || "")}</span>
          </div>
        </div>
      </article>`;
  }).join("")}</div>`;
}

const SPALTEN = [
  ["gewaesser", "Gewässer", "stark"], ["datum", "Datum", ""], ["koordinaten", "Koord.", "mono"],
  ["port", "Port", "mono"], ["fischart", "Fischart", "stark"], ["gewicht", "Gewicht", "gruen"],
  ["trophaee", "Trophäe", ""], ["koeder", "Köder", ""], ["dip", "Dip", ""], ["montage", "Montage", ""],
  ["tiefe", "Tiefe", ""], ["tageszeit", "Tageszeit", "leise"],
];

function tabelleHTML(spots) {
  const { feld, richtung } = zustand.sortierung;
  const kopf = SPALTEN.map(([f, t]) =>
    `<th data-sortieren="${f}" class="${f === feld ? "sortiert" : ""}">${t}<span class="pfeil">${f === feld && richtung > 0 ? "▲" : "▼"}</span></th>`
  ).join("");
  const zeilen = spots.map((s) => {
    const k = trophaeenKlasse(s.trophaee);
    const zellen = SPALTEN.map(([f, , klasse]) => {
      if (f === "trophaee") return `<td>${abzeichen(s.trophaee) || '<span class="leise">–</span>'}</td>`;
      const wert = f === "datum" ? datumDE(s.datum) : s[f];
      return `<td class="${klasse}" title="${esc(wert)}">${esc(wert) || '<span class="leise">–</span>'}</td>`;
    }).join("");
    return `<tr class="${k ? "t-" + k : ""}" data-id="${s.id}">${zellen}</tr>`;
  }).join("");
  return `<div class="tabelle-huelle"><table><thead><tr>${kopf}</tr></thead><tbody>${zeilen}</tbody></table></div>`;
}

/* ---------------- Editor ---------------- */
const form = $("#formular");

async function editorOeffnen(id = null) {
  if (zustand.editor && !(await aenderungenVerwerfen())) return;
  let spot = {};
  if (id) {
    try {
      spot = await api("GET", `spots/${id}`);
    } catch (e) {
      return toast(e.message, "fehler");
    }
  }
  zustand.editor = {
    id,
    trophaee: spot.trophaee || "",
    bilder: Object.fromEntries(BILD_FELDER.map((f) => [f, { name: spot[f] || null, neu: null }])),
    geaendert: false,
    aktivesBild: null,
    fischAlt: spot.fischart || null,
  };
  for (const f of TEXT_FELDER) form.elements[f].value = spot[f] ?? "";
  fischEditor.setzen(spot.fischart || "");
  if (!id) form.elements.datum.value = heuteISO();
  $$(".feld.fehler", form).forEach((el) => el.classList.remove("fehler"));
  segmentSetzen(zustand.editor.trophaee);
  BILD_FELDER.forEach(bildfeldZeichnen);

  $("#editor-titel").textContent = id ? (spot.fischart || "Spot bearbeiten") : "Neuer Spot";
  $("#editor-info").textContent = id
    ? `Spot #${id} · erstellt ${zeitDE(spot.erstellt)}${spot.geaendert && spot.geaendert !== spot.erstellt ? " · geändert " + zeitDE(spot.geaendert) : ""}`
    : "Pflichtfelder: Gewässer und Port";
  $("#btn-loeschen").hidden = !id;

  $("#schleier").hidden = false;
  const editor = $("#editor");
  editor.classList.add("offen");
  editor.setAttribute("aria-hidden", "false");
  setTimeout(() => form.elements.gewaesser.focus(), 120);
}

function editorSchliessenSofort() {
  zustand.editor = null;
  $("#editor").classList.remove("offen");
  $("#editor").setAttribute("aria-hidden", "true");
  $("#schleier").hidden = true;
}

async function aenderungenVerwerfen() {
  if (!zustand.editor?.geaendert) return true;
  return bestaetigen("Änderungen verwerfen?", "Du hast ungespeicherte Änderungen an diesem Spot.", "Verwerfen");
}

async function editorSchliessen() {
  if (await aenderungenVerwerfen()) editorSchliessenSofort();
}

function segmentSetzen(wert) {
  $$("#seg-trophaee button").forEach((b) => b.classList.toggle("aktiv", b.dataset.wert === wert));
}

function bildfeldZeichnen(feld) {
  const el = $(`.bildfeld[data-feld="${feld}"]`);
  const b = zustand.editor.bilder[feld];
  const quelle = b.neu || bildURL(b.name);
  el.classList.toggle("hat-bild", Boolean(quelle));
  $(".bildfeld-flaeche", el).innerHTML = quelle
    ? `<img src="${quelle}" alt="" data-bild-aktion="vollbild" title="Klicken für Vollbild">
       <div class="bild-aktionen">
         <button type="button" class="plus" data-bild-aktion="hinzufuegen" title="Anderen Screenshot wählen">${ICON.plus}</button>
         <button type="button" class="weg" data-bild-aktion="entfernen" title="Screenshot entfernen">${ICON.muell}</button>
       </div>
       ${b.neu ? '<span class="neu-markierung">NEU</span>' : ""}`
    : `<div class="hinweis">
         <button type="button" class="plus-gross" data-bild-aktion="hinzufuegen" title="Screenshot hinzufügen">${ICON.plus}</button>
         <span>Hinzufügen, hineinziehen<br>oder Strg+V</span>
       </div>`;
}

function dateiLesen(datei) {
  return new Promise((ok, fehler) => {
    const r = new FileReader();
    r.onload = () => ok(r.result);
    r.onerror = () => fehler(new Error("Datei konnte nicht gelesen werden."));
    r.readAsDataURL(datei);
  });
}

async function bildUebernehmen(feld, datei) {
  if (!datei || !zustand.editor) return;
  if (!/^image\/(png|jpeg|gif|bmp|webp)$/.test(datei.type)) {
    return toast("Bitte ein Bild wählen (PNG, JPG, GIF, BMP oder WebP).", "fehler");
  }
  if (datei.size > MAX_BILD_MB * 1024 * 1024) {
    return toast(`Das Bild ist größer als ${MAX_BILD_MB} MB.`, "fehler");
  }
  zustand.editor.bilder[feld].neu = await dateiLesen(datei);
  zustand.editor.geaendert = true;
  bildfeldZeichnen(feld);
}

function pruefen() {
  const fehler = [];
  const markieren = (name, meldung) => { form.elements[name].classList.add("fehler"); fehler.push(meldung); };
  $$(".feld.fehler", form).forEach((el) => el.classList.remove("fehler"));
  if (!form.elements.gewaesser.value.trim()) markieren("gewaesser", "Bitte ein Gewässer angeben.");
  if (!/^\d{4}$/.test(form.elements.port.value.trim())) markieren("port", "Der Port muss genau 4 Ziffern haben.");
  if (!fischEditor.festschreiben(true)) markieren("fischart", "Bitte eine Fischart aus der Liste wählen.");
  if (form.elements.datum.value && !/^\d{4}-\d{2}-\d{2}$/.test(form.elements.datum.value)) markieren("datum", "Ungültiges Datum.");
  if (fehler.length) {
    toast(fehler[0], "fehler");
    $(".feld.fehler", form)?.focus();
    return false;
  }
  return true;
}

async function speichern() {
  if (!zustand.editor || !pruefen()) return;
  const ed = zustand.editor;
  const daten = Object.fromEntries(TEXT_FELDER.map((f) => [f, form.elements[f].value.trim() || null]));
  daten.trophaee = ed.trophaee || null;
  for (const f of BILD_FELDER) daten[f] = ed.bilder[f].neu || ed.bilder[f].name || null;

  const knopf = $("#btn-speichern");
  knopf.disabled = true;
  knopf.textContent = "Speichert …";
  try {
    const spot = ed.id ? await api("PUT", `spots/${ed.id}`, daten) : await api("POST", "spots", daten);
    editorSchliessenSofort();
    toast(ed.id ? "Spot gespeichert" : "Spot angelegt");
    await metaLaden();
    await spotsLaden();
    const el = $(`[data-id="${spot.id}"]`);
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  } catch (e) {
    toast(e.message, "fehler");
  } finally {
    knopf.disabled = false;
    knopf.textContent = "Speichern";
  }
}

async function loeschen() {
  const ed = zustand.editor;
  if (!ed?.id) return;
  const name = form.elements.fischart.value.trim() || `Spot #${ed.id}`;
  if (!(await bestaetigen("Spot löschen?", `„${name}“ und alle zugehörigen Screenshots werden endgültig gelöscht.`, "Löschen"))) return;
  try {
    await api("DELETE", `spots/${ed.id}`);
    editorSchliessenSofort();
    toast("Spot gelöscht");
    await metaLaden();
    await spotsLaden();
  } catch (e) {
    toast(e.message, "fehler");
  }
}

function lightboxOeffnen(quelle) {
  const lb = $("#lightbox");
  $("img", lb).src = quelle;
  lb.hidden = false;
}

/* ---------------- Ereignisse ---------------- */
function ereignisseVerbinden() {
  // Kopf & Filter
  $("#btn-neu").addEventListener("click", () => editorOeffnen());
  const neuLaden = entprellen(spotsLaden);
  $("#suche").addEventListener("input", (e) => { zustand.filter.text = e.target.value; neuLaden(); });
  fischFilter = auswahlFeld($("#auswahl-filter-fisch"), {
    optionen: () => fischOptionen("filter"),
    beiWahl: (w) => { zustand.filter.fischart = w; spotsLaden(); },
    leerOption: "Alle Fischarten",
    meldungUnbekannt: "Bitte eine Fischart aus der Liste wählen.",
  });
  fischEditor = auswahlFeld($("#auswahl-fisch"), {
    optionen: () => fischOptionen("editor"),
    beiWahl: () => { if (zustand.editor) zustand.editor.geaendert = true; },
    meldungUnbekannt: "Diese Fischart gibt es nicht in der Liste – bitte auswählen.",
  });
  $("#f-gewaesser").addEventListener("change", (e) => { zustand.filter.gewaesser = e.target.value; spotsLaden(); });
  $("#f-trophaee").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    zustand.filter.trophaee = chip.dataset.wert;
    $$("#f-trophaee .chip").forEach((c) => c.classList.toggle("aktiv", c === chip));
    spotsLaden();
  });
  const zuruecksetzen = () => {
    zustand.filter = { text: "", gewaesser: "", fischart: "", trophaee: "" };
    $("#suche").value = "";
    fischFilter.setzen("");
    $("#f-gewaesser").value = "";
    $$("#f-trophaee .chip").forEach((c) => c.classList.toggle("aktiv", c.dataset.wert === ""));
    spotsLaden();
  };
  $("#f-reset").addEventListener("click", zuruecksetzen);

  $$(".umschalter button").forEach((b) => b.addEventListener("click", () => ansichtSetzen(b.dataset.ansicht, true)));

  // Inhalt: Karten/Zeilen anklicken, Sortieren
  $("#inhalt").addEventListener("click", (e) => {
    const th = e.target.closest("[data-sortieren]");
    if (th) {
      const f = th.dataset.sortieren;
      const s = zustand.sortierung;
      s.richtung = s.feld === f ? -s.richtung : (f === "datum" || f === "gewicht" || f === "trophaee" ? -1 : 1);
      s.feld = f;
      return zeichnen();
    }
    const aktion = e.target.closest("[data-aktion]")?.dataset.aktion;
    if (aktion === "neu") return editorOeffnen();
    if (aktion === "reset") return zuruecksetzen();
    const eintrag = e.target.closest("[data-id]");
    if (eintrag) editorOeffnen(Number(eintrag.dataset.id));
  });
  $("#inhalt").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.matches(".karte")) editorOeffnen(Number(e.target.dataset.id));
  });

  // Editor
  form.addEventListener("submit", (e) => { e.preventDefault(); speichern(); });
  form.addEventListener("input", () => { if (zustand.editor) zustand.editor.geaendert = true; });
  form.elements.port.addEventListener("input", (e) => { e.target.value = e.target.value.replace(/\D/g, "").slice(0, 4); });
  $("#btn-schliessen").addEventListener("click", editorSchliessen);
  $("#btn-abbrechen").addEventListener("click", editorSchliessen);
  $("#schleier").addEventListener("click", editorSchliessen);
  $("#btn-loeschen").addEventListener("click", loeschen);
  $("#seg-trophaee").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b || !zustand.editor) return;
    zustand.editor.trophaee = b.dataset.wert;
    zustand.editor.geaendert = true;
    segmentSetzen(b.dataset.wert);
  });

  // Bildfelder: Klick, Ziehen & Ablegen, Einfügen
  const dateiWahl = $("#datei-wahl");
  $$(".bildfeld").forEach((el) => {
    const feld = el.dataset.feld;
    el.addEventListener("focus", () => { if (zustand.editor) zustand.editor.aktivesBild = feld; });
    el.addEventListener("click", (e) => {
      if (!zustand.editor) return;
      zustand.editor.aktivesBild = feld;
      const aktion = e.target.closest("[data-bild-aktion]")?.dataset.bildAktion;
      const b = zustand.editor.bilder[feld];
      if (aktion === "entfernen") {
        b.neu = null;
        b.name = null;
        zustand.editor.geaendert = true;
        return bildfeldZeichnen(feld);
      }
      if (aktion === "vollbild") return lightboxOeffnen(b.neu || bildURL(b.name));
      if (aktion === "hinzufuegen") {
        dateiWahl.dataset.feld = feld;
        dateiWahl.value = "";
        dateiWahl.click();
      }
      // Klick auf leere Fläche: nur auswählen (Ziel für Strg+V), kein Dateidialog
    });
    el.addEventListener("keydown", (e) => {
      if ((e.key === "Delete" || e.key === "Backspace") && zustand.editor) {
        const b = zustand.editor.bilder[feld];
        if (b.neu || b.name) { b.neu = null; b.name = null; zustand.editor.geaendert = true; bildfeldZeichnen(feld); }
      }
    });
    el.addEventListener("dragover", (e) => { e.preventDefault(); el.classList.add("ziehen"); });
    el.addEventListener("dragleave", () => el.classList.remove("ziehen"));
    el.addEventListener("drop", (e) => {
      e.preventDefault();
      el.classList.remove("ziehen");
      bildUebernehmen(feld, e.dataTransfer.files[0]);
    });
  });
  dateiWahl.addEventListener("change", () => bildUebernehmen(dateiWahl.dataset.feld, dateiWahl.files[0]));
  document.addEventListener("paste", (e) => {
    const ed = zustand.editor;
    if (!ed) return;
    const datei = [...(e.clipboardData?.files || [])].find((f) => f.type.startsWith("image/"));
    if (!datei) return;
    e.preventDefault();
    // Ziel: angeklicktes Bildfeld, sonst das erste freie
    const ziel = ed.aktivesBild || BILD_FELDER.find((f) => !ed.bilder[f].neu && !ed.bilder[f].name) || "bild_trophaee";
    bildUebernehmen(ziel, datei);
  });
  // Bild versehentlich außerhalb fallen lassen: nicht im Fenster öffnen
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => e.preventDefault());

  // Lightbox
  $("#lightbox").addEventListener("click", () => { $("#lightbox").hidden = true; });

  // Tastenkürzel
  document.addEventListener("keydown", (e) => {
    const strg = e.ctrlKey || e.metaKey;
    if (e.key === "Escape") {
      if (!$("#lightbox").hidden) { $("#lightbox").hidden = true; return; }
      if (zustand.editor) { editorSchliessen(); return; }
    }
    if (strg && e.key.toLowerCase() === "s" && zustand.editor) { e.preventDefault(); speichern(); }
    if (strg && e.key.toLowerCase() === "n") { e.preventDefault(); editorOeffnen(); }
    if (strg && e.key.toLowerCase() === "f") { e.preventDefault(); $("#suche").focus(); }
  });
}

function ansichtSetzen(ansicht, speichernJa = false) {
  zustand.ansicht = ansicht === "tabelle" ? "tabelle" : "karten";
  $$(".umschalter button").forEach((b) => b.classList.toggle("aktiv", b.dataset.ansicht === zustand.ansicht));
  zeichnen();
  if (speichernJa) api("PUT", "einstellungen", { ansicht: zustand.ansicht }).catch(() => {});
}

/* ---------------- Start ---------------- */
(async function start() {
  ereignisseVerbinden();
  try {
    const einstellungen = await api("GET", "einstellungen");
    ansichtSetzen(einstellungen.ansicht || "karten");
    await metaLaden();
    await spotsLaden();
  } catch (e) {
    toast(e.message, "fehler");
  }
})();
