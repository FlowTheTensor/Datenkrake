<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Forgejo: Agiles Arbeiten mit Scrum light und Kanban

Forgejo ist eine selbst gehostete Git-Plattform, vergleichbar mit GitHub, die
als Container auf dem Raspberry läuft. Im Unterricht nutzen wir davon vor
allem drei Dinge:

| Funktion | Wofür |
|---|---|
| **Issues** | Das Backlog: jede Aufgabe, jeder Fehler ist ein Issue. Schüler legen eigene Issues an. |
| **Projekt-Board** | Das Kanban-Board mit Spalten von „Backlog“ bis „Erledigt“. |
| **Commits** | Der automatische Deploy-Verlauf von Node-RED. Jeder Deploy im Editor erscheint hier als Commit und kann in Issues verlinkt werden. |

Alles bleibt im Schulnetz auf dem Raspberry. Es gibt keine Selbstregistrierung,
Konten legt die Lehrkraft an, und ohne Anmeldung ist nichts sichtbar. Das
Datenkrake-Repo auf GitHub bleibt davon unberührt.

```text
Node-RED-Editor ──Deploy──► ~/nodered-verlauf (Git, lokal) ──push──► Forgejo: datenkrake-projekt
                                                                       ├─ Commits = Deploy-Verlauf
                                                                       ├─ Issues  = Backlog
                                                                       └─ Projekt = Kanban-Board
```

Aufruf: **<http://datenkrake.local:3001>**

## Einrichtung (Lehrkraft, einmalig)

Forgejo wird von `setup_iot_stack.sh` bzw. `update_iot_stack.sh` als Container
mitgestartet (Dienst `forgejo` in `compose/docker-compose.yml`, Daten in
`Raspberry/forgejo/data/`). Danach auf dem Raspberry im Repo-Ordner:

```bash
cd Raspberry/forgejo

# 1. Eigenes Admin-Konto anlegen (Passwort wird abgefragt)
./forgejo_einrichten.sh lehrkraft lehrkraft

# 2. Projekt-Repo mit Labels, Issue-Vorlagen und Deploy-Verlauf einrichten
./forgejo_einrichten.sh projekt lehrkraft

# 3. Schülerkonten anlegen und ins Projekt aufnehmen
cp schueler.beispiel.txt schueler-efs02.txt   # Namen eintragen
./forgejo_einrichten.sh schueler schueler-efs02.txt lehrkraft
```

Schritt 3 schreibt die Startpasswörter in `konten-<datum>.csv`. Die Datei
ausdrucken bzw. verteilen und danach löschen. Beim ersten Login muss jeder
sein Passwort ändern. Für die Benutzernamen reichen Vornamen oder Kürzel,
z. B. `anna.m`, ohne Team im Namen: Die Teams werden später zugeordnet
(siehe [Teams zuordnen](#teams-zuordnen)). Kommen Schüler dazu, die Liste
ergänzen und den Befehl erneut ausführen; bestehende Konten bleiben
unverändert. Namenslisten und CSV-Dateien sind per `.gitignore`
vom Commit ausgeschlossen.

Schritt 2 setzt außerdem einen Branchschutz: Auf `main` im Projekt-Repo darf
nur der Verlauf-Dienst pushen, Schüler arbeiten ausschließlich mit Issues und
Board. Dateien in diesem Repo deshalb **nicht** über die Weboberfläche ändern,
sonst schlägt der automatische Push des Deploy-Verlaufs fehl.

### Teams zuordnen

Ein Team ist eine Station. Konten müssen dafür nicht geändert werden, die
Zuordnung entsteht an drei Stellen:

- **Issues und Board:** Label `station/…` der Station setzen und die
  Teammitglieder als *Zuständige* (Assignees) eintragen. Über den
  Label-Filter sieht jedes Team seine Karten.
- **Node-RED:** Das Team arbeitet im Tab seiner Station; die Commits im
  Deploy-Verlauf tragen automatisch den Tab-Namen als Autor.
- **Teameinteilung festhalten:** in einem angepinnten Issue, z. B.
  „Teameinteilung Sprint 1“, mit einer Tabelle Station → Schüler. Bei neuer
  Einteilung ein neues Issue anlegen, dann bleibt nachvollziehbar, wer wann
  in welchem Team war.

Konten, die schon mit einem Team im Namen angelegt wurden, lassen sich als
Admin umbenennen: *Website-Administration → Benutzerkonten → Konto
bearbeiten → Benutzername*.

### Kanban-Board anlegen (in der Weboberfläche)

Für Boards hat Forgejo keine API, deshalb einmal von Hand:

1. Im Repo `datenkrake-projekt` → **Projekte** → **Neues Projekt**, Name z. B.
   „EFS02 Schuljahr 2026/27“, Vorlage **Basic Kanban**.
2. Spalten umbenennen bzw. ergänzen, sodass sie so aussehen:

   | Backlog | Bereit | In Arbeit | Test | Erledigt |
   |---|---|---|---|---|
   | alle Ideen und Aufgaben | Akzeptanzkriterien sind klar, Sprint ist geplant | ein Team arbeitet daran | ein anderes Team prüft | PO hat abgenommen |

3. Unter **Meilensteine** pro Sprint einen Meilenstein mit Enddatum anlegen,
   z. B. „Sprint 1 – OPC-UA-Daten verlässlich“.

### Labels

| Label | Bedeutung |
|---|---|
| `story` | Neue Funktion aus Sicht der Nutzer |
| `bug` | Etwas funktioniert nicht wie erwartet |
| `opc-ua` | OPC-UA-Abfrage der SPS-Stationen |
| `node-red` | Flows im Node-RED-Editor |
| `grafana` | Dashboards und Auswertung |
| `doku` | Dokumentation und Erklärungen |
| `blockiert` | Team kommt ohne Hilfe nicht weiter |
| `station/01-leitstand` … `station/09-transfersystem-roboter` | Zuständiges Stationsteam. Pro Issue nur eine Station; über diese Labels filtert jedes Team Board und Issues nach seinen Aufgaben. |

## Arbeitsablauf für Schülerinnen und Schüler

1. **Issue nehmen:** Auf dem Board ein Issue aus „Bereit“ wählen, sich (bzw.
   das Team) zuweisen und die Karte nach „In Arbeit“ ziehen.
2. **Im Stations-Tab arbeiten:** Jedes Team ist für eine SPS-Station
   zuständig und arbeitet in Node-RED nur in deren Tab, z. B.
   „Station 03 Rohlager Dosen“. Die abgefragten Knoten stehen im
   Template-Node **NodesAuswahl** und können dort ergänzt werden. Die Daten
   des Tabs erscheinen auf MQTT `team/<station>/<tag>` und landen getrennt
   von den Produktionsdaten in der Datenbank. Im digitalen Zwilling lässt
   sich das eigene Team auswählen und mit der Produktion vergleichen. Details:
   [Stations-Tabs](../nodered/README.md#stations-tabs-für-die-stationsteams).
3. **Deployen:** Jeder Deploy wird automatisch gesichert und erscheint
   kurz danach als Commit im Projekt-Repo, mit dem Stationsteam als Autor
   und einer Zusammenfassung wie `+2 / -0 / ~1 Nodes`. Den eigenen Verlauf
   zeigt Forgejo unter **Code → flows → station-…json → Verlauf**.
4. **Fortschritt dokumentieren:** Am Ende jeder Stunde einen kurzen
   Kommentar ins Issue schreiben: was geschafft, was als Nächstes, was hakt.
   Den Deploy-Commit verlinken, indem man seinen Hash (z. B. `a6a7ae4`)
   im Kommentar nennt; Forgejo macht daraus automatisch einen Link.
5. **Test:** Karte nach „Test“ ziehen. Ein anderes Team prüft die
   Akzeptanzkriterien und hakt sie ab.
6. **Abnahme:** Die Lehrkraft (Product Owner) schließt das Issue, die Karte
   wandert nach „Erledigt“.

Eigene Ideen und gefundene Fehler: **Neues Issue** → Vorlage „User Story“ oder
„Fehler melden“ wählen. Neue Issues landen im Backlog, priorisiert werden sie
im Sprint Planning.

**Wichtig in Node-RED:**

- Meldet der Editor beim Deploy, dass die Flows auf dem Server inzwischen
  geändert wurden, **zuerst zusammenführen** (Merge), nie einfach
  überschreiben – sonst geht die Arbeit eines anderen Teams verloren.
  Verloren wäre sie trotzdem nicht endgültig: Die Lehrkraft kann jeden
  Stations-Tab einzeln auf einen früheren Stand zurücksetzen, siehe
  [Flow-Verlauf](../nodered/README.md#flow-verlauf-änderungen-der-schüler-sichern).
- Neue OPC-UA-Abfragen zuerst gegen den Demo-Server (`opcua_demo_server`)
  testen. Die echten SPSen haben nur begrenzt viele OPC-UA-Sitzungen.
- Ein Tab lässt sich über seine Eigenschaften deaktivieren, statt ihn zu
  löschen.

## Scrum light im Unterricht

Scrum ist für Vollzeit-Teams gedacht. Im Unterricht arbeiten wir in
Unterrichtsblöcken mit Pausen von mehreren Tagen dazwischen, deshalb eine
schlanke Variante.

### Rollen

| Rolle | Wer | Aufgabe |
|---|---|---|
| **Product Owner (PO)** | Lehrkraft | Pflegt und priorisiert das Backlog, beantwortet fachliche Fragen, nimmt Ergebnisse ab. |
| **Scrum Master** | wechselt pro Sprint (ein Schüler) | Moderiert Stand-up und Retro, hält das Board aktuell, meldet Blockaden an den PO. |
| **Stationsteams** | Teams aus 2–3 Schülern, je eins pro SPS-Station (bis zu 9) | Betreuen ihren Stations-Tab, setzen Issues um, testen gegenseitig. |

### Rhythmus

| Termin | Wann | Dauer | Inhalt |
|---|---|---|---|
| **Sprint Planning** | erster Block des Sprints | 20–30 min | PO stellt die wichtigsten Issues vor, Teams schätzen sie (T-Shirt-Größen S/M/L) und ziehen so viele nach „Bereit“, wie realistisch sind. Sprintziel als Meilenstein festhalten. |
| **Stand-up** | Beginn jedes Blocks | 5–10 min | Am Board, jedes Team: Was haben wir geschafft? Was machen wir heute? Wo hängen wir? Blockierte Karten bekommen das Label `blockiert`. |
| **Arbeitsphase** | jeder Block | Rest | Umsetzen, Lehrkraft unterstützt bei `blockiert`. |
| **Abschluss** | Ende jedes Blocks | 5 min | Board aktualisieren, Kommentar ins Issue. |
| **Sprint Review** | letzter Block des Sprints | 20–30 min | Live-Vorführung an der Anlage, im Zwilling oder in Grafana. PO nimmt ab oder schickt zurück. |
| **Retrospektive** | direkt nach dem Review | 15 min | Start / Stop / Continue: Was fangen wir an, was lassen wir, was behalten wir bei? Ergebnisse als Kommentar im Sprint-Meilenstein. |

Sinnvolle Sprintlänge: **3–4 Unterrichtsblöcke** (also etwa 2–4 Wochen).

### Regeln

- **WIP-Limit:** Pro Team höchstens **ein** Issue in „In Arbeit“. Erst
  fertig machen, dann Neues anfangen.
- **Definition of Ready** (darf nach „Bereit“): Die Story ist verständlich
  formuliert, hat prüfbare Akzeptanzkriterien und passt in einen Sprint. Zu
  große Stories teilt der PO mit dem Team auf.
- **Definition of Done** (darf nach „Erledigt“):
  - läuft auf dem Raspberry (deployt, Deploy-Commit im Issue verlinkt),
  - alle Akzeptanzkriterien abgehakt,
  - von einem anderen Team getestet,
  - kurz dokumentiert (Kommentar im Issue oder Kommentar-Node im Flow),
  - vom PO abgenommen.

### Leistungsbewertung (Anregung)

Forgejo zeigt pro Person Issues, Kommentare und Board-Bewegungen. Die
Issue-Kommentare am Ende jedes Blocks dienen als Lernjournal und
Nachweis der eigenen Arbeit, die Sprint Reviews als Präsentationsleistung.

## Startbacklog: OPC-UA-Daten verlässlich abfragen

Der größte offene Punkt ist die verlässliche Abfrage der OPC-UA-Daten
(siehe `todo.md`). Vorschläge für erste Issues, die sich in Node-RED umsetzen
lassen:

| # | Issue | Labels |
|---|---|---|
| 1 | Als Instandhalter möchte ich, dass jeder Tag mindestens einmal pro Sekunde gelesen wird, damit keine Werte veraltet sind. Drossel „Drosseln (20 msg/s)“ im Flow untersuchen: Wie viele Read-Nachrichten entstehen pro Sekunde, wie lang wird die Warteschlange? | `opc-ua`, `node-red` |
| 2 | Als Schichtleitung möchte ich wissen, ob kurze Bandsensor-Impulse verloren gehen. Einen einzelnen Bandsensor per Subscribe mit 100 ms beobachten und die Zahl der Impulse mit der Zahl der durchgelaufenen Werkstücke vergleichen. | `opc-ua`, `node-red` |
| 3 | Als Instandhalter möchte ich die Flankenzähler aus der SPS (sobald angelegt) lesen und per MQTT veröffentlichen, damit kein Impuls mehr fehlt. | `opc-ua`, `node-red` |
| 4 | Als Lagerverwaltung möchte ich den Füllstand des Palettenlagers erst messen, wenn die Auslagerung abgeschlossen ist (`AL-BG2_Bandsensor_Rechts` aktiv). | `node-red` |
| 5 | Als neues Teammitglied möchte ich verstehen, wozu `NodesAuswahl.txt` dient und wie sie aufgebaut ist. | `doku` |
| 6 | Als Schichtleitung möchte ich in Grafana sehen, wie viele Bandsensor-Impulse pro Station und Stunde ankommen. | `grafana` |

## Ausblick: Phase 2 mit Code-Änderungen

Solange die Schüler nur Flows ändern, reicht das Projekt-Repo mit dem
Deploy-Verlauf. Sollen später auch Dateien wie Skripte oder Dashboards
geändert werden, kommt ein zweites Repo in Forgejo dazu (Kopie des
Datenkrake-Repos). Schüler arbeiten dort mit Branches und Pull Requests, die
Lehrkraft übernimmt Gelungenes auf dem eigenen Rechner und pusht es selbst
nach GitHub. Der Raspberry pusht nie nach GitHub.

## Betrieb

- **Sicherung:** Alle Forgejo-Daten (SQLite-Datenbank, Repos, Anhänge) liegen
  in `Raspberry/forgejo/data/` und sind Teil der Datensicherung auf USB-Stick,
  siehe [backup/README.md](../backup/README.md). Nur Forgejo zurückspielen:
  `sudo ./Raspberry/backup/wiederherstellen.sh <sicherung> forgejo`.

- **Passwort vergessen:**
  `docker exec -u git forgejo forgejo admin user change-password --username <name> --password <neu>`
- **Speicher:** Forgejo braucht mit SQLite etwa 150–250 MB RAM.
- **Port:** Weboberfläche 3001 (3000 ist von Grafana belegt), Git über SSH
  auf 2222.
