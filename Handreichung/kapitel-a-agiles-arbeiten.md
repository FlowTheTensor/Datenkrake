# Kapitel A · Agiles Arbeiten: Scrum light und Kanban

[← Übersicht](README.md)

## Worum es geht

Die Datenkrake ist nicht fertig, und daran arbeitet die Klasse weiter.
Stationsteams aus 2–3 Personen betreuen je eine SPS-Station, organisiert mit
einer schlanken Scrum-Variante und einem Kanban-Board in Forgejo auf dem
Raspberry. Jeder Deploy im Node-RED-Editor wird automatisch als Commit
gesichert und dient als Arbeitsnachweis.

Dieses Kapitel ist weniger ein Lerninhalt als der **organisatorische Rahmen**
für die übrigen Kapitel. Die ausführliche Anleitung mit Einrichtung, Rollen,
Rhythmus, Regeln und Startbacklog steht in
[`Raspberry/forgejo/README.md`](../Raspberry/forgejo/README.md).

## Lernziele

Die Schülerinnen und Schüler können …

- eine Aufgabe als User Story mit prüfbaren Akzeptanzkriterien formulieren,
- den Weg eines Issues über das Kanban-Board beschreiben (Backlog → Bereit → In Arbeit → Test → Erledigt),
- die Rollen Product Owner, Scrum Master und Team unterscheiden,
- ihre Arbeit nach der Definition of Done prüfen und nachweisen (Deploy-Commit im Issue),
- in einer Retrospektive die Zusammenarbeit reflektieren.

## Voraussetzungen

Ausbaustufe 1: Raspberry mit Forgejo und Node-RED, Schülerkonten angelegt
(`forgejo_einrichten.sh`). Für echte Stationsarbeit Ausbaustufe 3.

## Zeitbedarf und Ablauf

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einführung | 1 DS | Rollen und Board erklären, Konten verteilen, jedes Team stellt ein erstes Issue ein |
| Sprint Planning | 20–30 min | Issues schätzen (S/M/L), Sprintziel festlegen |
| je Unterrichtsblock | 5–10 min + 5 min | Stand-up zu Beginn, Board und Issue-Kommentar am Ende |
| Sprint Review + Retro | 30–45 min | Vorführung an Anlage, Zwilling oder Grafana, danach Start/Stop/Continue |

Ein Sprint umfasst 3–4 Unterrichtsblöcke.

## Aufgaben und Musterlösungen

### Lernpfad „Automatisierer“, Schritt 7: Selbst verbessern

> Stellt im Backlog ein Issue ein: Was würdet ihr am Abgriff eurer Station verbessern? Formuliert Akzeptanzkriterien.

**Erwartung:** ein Issue im Format „Als … möchte ich …, damit …“ mit 2–4
Akzeptanzkriterien, die man **prüfen** kann, und dem Label der eigenen Station.

**Beispiel einer guten Lösung:**

> **Als** Instandhalter **möchte ich**, dass jeder Durchlauf eines Werkstückträgers
> am Bandsensor rechts gezählt wird, **damit** ich verlorene Impulse erkennen kann.
>
> Akzeptanzkriterien:
> - [ ] Der Bandsensor wird per Subscribe statt per Read abgefragt (Abtastintervall 100 ms).
> - [ ] Über 10 Minuten stimmt die Zahl der Impulse mit der Zahl der durchgelaufenen Werkstücke überein (Strichliste an der Anlage).
> - [ ] Die Daten erscheinen unter `team/<station>/…` in der Datenbank.
>
> Labels: `opc-ua`, `node-red`, `station/04-abfuellen`

**Typische schwache Lösungen:** „Node-RED verbessern“ (keine Story, nicht
prüfbar), Kriterien wie „funktioniert besser“, mehrere Stationen in einem Issue.
Weitere Beispiele bietet das Startbacklog in der Forgejo-README.

## Typische Schwierigkeiten

- **Zu große Issues.** Ein Issue soll in einen Sprint passen. Zu große Stories
  gemeinsam teilen, statt sie wochenlang „In Arbeit“ stehen zu lassen.
- **WIP-Limit wird umgangen.** Teams ziehen mehrere Issues gleichzeitig nach
  „In Arbeit“. Konsequent auf eins pro Team achten.
- **Deploy überschreibt fremde Arbeit.** Meldet Node-RED beim Deploy, dass die
  Flows auf dem Server geändert wurden, erst zusammenführen. Notfalls lässt sich
  jeder Tab über den Flow-Verlauf zurücksetzen
  ([`Raspberry/nodered/README.md`](../Raspberry/nodered/README.md)).
- **Issue-Kommentare bleiben leer.** Den 5-Minuten-Abschluss jedes Blocks fest
  einplanen, sonst fehlt später der Nachweis.
- **Retro wird zur Beschwerderunde.** Bei Start/Stop/Continue auf konkrete,
  umsetzbare Punkte achten und einen davon im nächsten Sprint wirklich ausprobieren.

## Bewertung

Forgejo zeigt pro Person Issues, Kommentare und Bewegungen auf dem Board. Für
eine Bewertung bieten sich an:

| Nachweis | Woran man gute Arbeit erkennt |
| --- | --- |
| Issues | Story-Format, prüfbare Akzeptanzkriterien, passende Labels |
| Kommentare (Lernjournal) | regelmäßig, nachvollziehbar: was gemacht, was gelernt, wo hängt es |
| Deploy-Commits | im Issue verlinkt, zum Issue passend |
| Test für ein anderes Team | Kriterien wirklich geprüft, Befund dokumentiert |
| Sprint Review | Ergebnis an Anlage, Zwilling oder Grafana gezeigt, Akzeptanzkriterien belegt |

## Material im Repo

- [`Raspberry/forgejo/`](../Raspberry/forgejo): Einrichtung, Issue-Vorlagen, Startbacklog
- [`Raspberry/nodered/verlauf/`](../Raspberry/nodered/verlauf): automatischer Deploy-Verlauf
- Quiz Kapitel A auf der Hauptseite
