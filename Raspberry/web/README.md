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
- `content/chat.html`, `content/thema-*.html`, `content/quiz.html` und `content/technologien.html` enthalten die einzelnen Inhaltsbereiche.
- `content-loader.js` laedt die HTML-Fragmente und startet danach `index.js`.

Bei kuenftigen Aenderungen sollte nur die jeweils zustaendige Datei geoeffnet
werden. Das spart Kontext und Token. Bilder werden als eigene Dateien aus dem
Webroot geladen und nicht als Base64 in HTML eingebettet.