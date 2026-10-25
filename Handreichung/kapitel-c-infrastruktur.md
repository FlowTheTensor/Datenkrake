# Kapitel C · Infrastruktur & Hardware

[← Übersicht](README.md)

## Worum es geht

Alle Dienste der Datenkrake laufen als Docker-Container auf einem Raspberry Pi,
dem zentralen **Edge-Server**. Der Arduino UNO Q rechnet direkt am Mikrofon
(Edge AI). Der Pi verbindet zwei Netze, die sonst getrennt sind: das
**Anlagen-Netz** mit den Steuerungen und das **DMZ-Netz** der Schule.

## Lernziele

Die Schülerinnen und Schüler können …

- die Geräte der Datenkrake und ihre Aufgaben benennen (Architekturbild),
- erklären, warum Anlagen-Netz und Schulnetz getrennt sind und welche Rolle der Pi dabei spielt,
- den Nutzen von Containern gegenüber einer direkten Installation begründen,
- Edge Computing von einer Verarbeitung in der Cloud abgrenzen.

## Voraussetzungen

Ausbaustufe 0 zum Lesen. Praktisch ab Stufe 1, z. B. mit `docker compose ps` im
Ordner `Raspberry/compose`.

## Zeitbedarf und Ablauf

1–2 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 15 min | Architekturbild gemeinsam lesen: Was steht wo? |
| Netzwerk | 30 min | Netzwerktopologie, Aufgabe „Zwei Netze, ein Pi“ |
| Container | 30 min | Was ist ein Container? Am Pi: `docker compose ps`, Container neu starten, Logs ansehen |
| Sicherung | 15 min | Quiz Kapitel C |

## Aufgaben und Musterlösungen

### Lernpfad „Erster Überblick“, Schritt 2: Was steht wo?

> Öffnet die Architektur. Zählt, welche Geräte beteiligt sind, und zeigt auf den Rechner, der „die Datenkrake“ ist.

**Musterlösung:** Beteiligt sind

1. die **Modellanlage** mit ihren SPS-Stationen,
2. der **Arduino UNO Q** als Akustik-KI (ein zweiter für das YOLO-System ist geplant),
3. der **Raspberry Pi 5**: Das ist „die Datenkrake“ mit Broker, Datenbanken, Node-RED und Webserver,
4. ein **Server/PC** für den Data Lake,
5. ein **PC mit MCP-Server und Claude Desktop**,
6. der **Browser** bzw. Laptop,
7. das **Diagnosegerät** des Wartungs-Agenten.

Ob das YOLO-System mitgezählt wird, ist Auslegungssache. Wichtig ist, dass der
Pi als zentraler Knoten erkannt wird, über den alle Daten laufen.

### Lernpfad „Automatisierer“, Schritt 1: Zwei Netze, ein Pi

> Warum hängt der Raspberry in zwei Netzen, und warum kommt euer Laptop nicht direkt an die SPS?

**Musterlösung:**

- Der Pi hängt per **Ethernet im Anlagen-Netz** `192.168.36.0/24`, dort liegen
  die SPS-Stationen. Er braucht diesen Zugang, um die Werte per OPC-UA zu lesen.
- Per **WLAN** ist er zusätzlich **Client im DMZ-Netz** der Schule. Dort sind
  Laptops und Arduino, und von dort ruft man die Webseiten auf.
- **Zwischen den Netzen wird nicht geroutet.** Der Laptop erreicht deshalb nur
  den Pi, nie die Steuerungen.
- **Grund:** Steuerungen sind empfindlich und meist nicht gegen Angriffe
  geschützt. Ein versehentlicher Schreibzugriff, Schadsoftware auf einem Laptop
  oder zu viele Abfragen könnten die Anlage stören. Der Pi ist die einzige,
  kontrollierte Brücke, und er liest nur.

**Stufe 4** erreicht, wer den Bezug zur IT-Sicherheit in der Industrie herstellt
(Netzsegmentierung) oder fragt, was passiert, wenn der Pi selbst kompromittiert
wird.

### Lernpfad „KI-Agenten-Bauer“, Schritt 1: Wer redet mit wem?

> Öffnet die Architektur und verfolgt die Pfeile zwischen den Agenten. Welche Verbindung ist MCP, welche A2A, welche LAP?

**Musterlösung:**

| Protokoll | Verbindung im Architekturbild | Art der Verbindung |
| --- | --- | --- |
| **MCP** | MCP-Server ↔ Claude Desktop | Sprachmodell ↔ Werkzeuge und Daten („vertikal“) |
| **A2A** | Orchestrator-Agent → DB-Agent, Report-Agent, Wartungs-Agent | Agent ↔ Agent („horizontal“) |
| **LAP** | Wartungs-Agent → Zusatzgerät (Diagnose) | Agent ↔ physisches Gerät, nur nach Sicherheitsbestätigung |

Wichtig ist der Hinweis im Bild: Der Wartungs-Agent greift **nie** auf die
Modellanlage zu, nur auf sein eigenes Diagnosegerät.

## Typische Schwierigkeiten

- **Container mit virtueller Maschine verwechseln.** Container teilen sich den
  Kernel des Pi und bringen nur die eigene Software mit. Deshalb laufen gut zehn
  davon auf einem Raspberry.
- **`datenkrake.local` geht nicht.** Der Name wird per mDNS aufgelöst. Manche
  Schulnetze oder Windows-Geräte blockieren das, dann hilft die IP-Adresse des Pi.
- **„Der Pi ist ein Router.“** Er verbindet zwar beide Netze, leitet aber nichts
  weiter. Er ist kein Access Point und kein Gateway.
- **Edge = „kleiner Rechner“.** Gemeint ist der Ort der Verarbeitung, nahe an der
  Datenquelle, nicht die Größe des Geräts.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Geräte und Netze werden richtig benannt.
- Stufe 3: Die Netztrennung wird mit Sicherheitsgründen erklärt.
- Stufe 4: Es wird abgewogen, was die Trennung kostet (z. B. kein Fernzugriff auf die SPS) und wie ein Angriff auf den Pi abgefangen werden könnte.

## Material im Repo

- [`Raspberry/compose/`](../Raspberry/compose): alle Container und Ports
- [`Raspberry/README.md`](../Raspberry/README.md): Installation, Container, Ports
- [`architektur-komponenten.md`](../architektur-komponenten.md): vollständige Komponentenübersicht
- [`Images/architektur.svg`](../Images/architektur.svg)
- Quiz Kapitel C auf der Hauptseite
