<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Weboberflaeche

Dieser Ordner enthaelt die Apache/PHP-Weboberflaeche mit Leitstand sowie getrennten Audio- und PLC-Uebersichten.

Der Dienst wird ueber Docker Compose gestartet und ist auf Port `80` erreichbar. `index.html` ist die Startseite, `audiodaten.php` und `plcdaten.php` sind die Datenuebersichten. Die Endpunkte liegen unter `api/`, die gemeinsame Datenbankverbindung unter `includes/db.php`.

## Hauptseite modular bearbeiten

Die Hauptseite ist bewusst in drei Dateien getrennt:

- `index.html` enthaelt nur die Seitenstruktur und Inhalte.
- `index.css` enthaelt das komplette Layout und Styling.
- `index.js` enthaelt Interaktionen, API-Aufrufe, Agent-Cards und Quizlogik.
- `content/hero.html` enthaelt den Einstiegsbereich.
- `content/chat.html`, `content/thema-*.html`, `content/quiz.html` und `content/glossar.html` enthalten die einzelnen Inhaltsbereiche.
- `content-loader.js` laedt die HTML-Fragmente und startet danach `index.js` und `glossar.js`.
- `content/glossar.json` enthaelt alle Glossarbegriffe, `glossar.js` baut daraus den Glossar-Bereich und die Tooltips.
- `reise-eines-messwerts.html` ist eine eigenstaendige Vertiefungsseite (SPS-Impuls und Akustikmessung Schritt fuer Schritt). Die Inhalte stehen als Liste `REISEN` im Skript der Seite. Bereiche mit `data-glossar-bereich` bekommen ebenfalls Glossar-Tooltips.

## Glossar erweitern

Neue Begriffe werden nur in `content/glossar.json` eingetragen, Code muss dafuer
nicht angefasst werden:

```json
{
  "id": "deadband",
  "begriff": "Deadband",
  "kategorie": "Anlage & Datenerhebung",
  "kurz": "Ein Satz fuer den Tooltip.",
  "datenkrake": "Was der Begriff bei uns bedeutet (optional).",
  "treffer": ["Deadband", "Deadbands"],
  "kapitel": ["D"],
  "siehe": ["opc-ua"]
}
```

- `kategorie` muss einer der Eintraege in `kategorien` sein.
- `treffer` sind die Schreibweisen, die in den Kapiteln automatisch unterstrichen
  werden. Gross-/Kleinschreibung zaehlt, Mehrzahl und Beugungen extra eintragen.
  Markiert wird pro Kapitel nur das erste Vorkommen.
- `kapitel` sind die Kapitelbuchstaben A–H, `siehe` die `id` anderer Begriffe.
- Nicht markiert werden Ueberschriften, Links, Buttons, Code, Diagramme und das
  Quiz (damit Tooltips keine Antworten verraten). Soll ein Bereich sonst frei
  bleiben, bekommt er das Attribut `data-kein-glossar`.
- Direktlink auf einen Eintrag: `index.html#glossar-<id>`.

Bei kuenftigen Aenderungen sollte nur die jeweils zustaendige Datei geoeffnet
werden. Das spart Kontext und Token. Bilder werden als eigene Dateien aus dem
Webroot geladen und nicht als Base64 in HTML eingebettet.