<img align="right" src="../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# Handreichung für Lehrkräfte

Diese Handreichung begleitet die Hauptseite der Datenkrake
([online](https://flowthetensor.github.io/Datenkrake/) bzw. `http://datenkrake.local`).
Für jedes der acht Kapitel A–H gibt es eine eigene Seite mit Lernzielen,
Zeitbedarf, einem Ablaufvorschlag, den Aufgaben aus den Lernpfaden samt
**Musterlösungen**, typischen Schwierigkeiten und Hinweisen zur Bewertung.

Welche Hardware für welches Kapitel nötig ist, steht in den
[Ausbaustufen](../AUSBAUSTUFEN.md).

> **Hinweis:** Die Musterlösungen stehen öffentlich im Repository. Wer sie für
> Leistungsnachweise nutzt, sollte die Aufgaben leicht abwandeln, etwa durch
> eine andere Station oder ein anderes Signal.

## Kapitel

| Kapitel | Thema | Zeit (Richtwert) | Ab Ausbaustufe |
| --- | --- | --- | --- |
| [A](kapitel-a-agiles-arbeiten.md) | Agiles Arbeiten: Scrum light, Kanban, Forgejo | 1 DS Einführung, danach begleitend | 1 |
| [B](kapitel-b-crisp-dm.md) | Theoretischer Unterbau: CRISP-DM | 1 DS | 0 |
| [C](kapitel-c-infrastruktur.md) | Infrastruktur & Hardware | 1–2 DS | 0, praktisch ab 1 |
| [D](kapitel-d-datenerhebung.md) | Datenerhebung: Akustik, SPS-Signale, digitaler Zwilling | 2 DS | 0, praktisch ab 2/3 |
| [E](kapitel-e-kommunikation.md) | Kommunikation & Industrie 4.0: OPC-UA, MQTT, Node-RED | 2–3 DS | 1 |
| [F](kapitel-f-datenhaltung.md) | Datenhaltung und -analyse | 2 DS | 1 |
| [G](kapitel-g-machine-learning.md) | Machine Learning und Anomalie-Erkennung | 3–4 DS | 1, mit echten Daten ab 2 |
| [H](kapitel-h-agentensysteme.md) | Agentensysteme: MCP, A2A, LAP | 2–3 DS | 0, praktisch ab 4 |

DS = Doppelstunde (90 min). Die Zeiten sind grobe Schätzungen für eine Klasse,
die das Thema neu kennenlernt, und hängen stark von den Vorkenntnissen ab.

## Wie man die Datenkrake im Unterricht einsetzen kann

**Als Lernsituation über mehrere Wochen.** Die Klasse durchläuft CRISP-DM
einmal komplett: von der Frage „Woran erkennen wir, dass mit der Anlage etwas
nicht stimmt?“ (B) über die Datenerhebung (D, E) und Datenhaltung (F) bis zum
Modell (G) und zur Reaktion der Agenten (H). Kapitel A liefert dazu den
organisatorischen Rahmen mit Sprints und Stationsteams.

**Mit Lernpfaden, differenziert nach Interesse.** Auf der Hauptseite können die
Schülerinnen und Schüler einen von vier Lernpfaden wählen:

| Lernpfad | Kapitel in dieser Reihenfolge | Schwerpunkt |
| --- | --- | --- |
| Erster Überblick | B → C → Reise eines Messwerts → D → H | Einstieg für alle |
| Automatisierer | C → D → E → Reise (Halt 3/4) → E → F → A | SPS, OPC-UA, Node-RED, MQTT |
| Datenanalyst | B → D → Reise (Akustik) → F → G → G | Datenbanken, CRISP-DM, ML |
| KI-Agenten-Bauer | C → G → H → H → LangGraph-Werkstatt → H | MCP, A2A, LAP |

Ein möglicher Ablauf: Alle starten mit „Erster Überblick“, danach wählen Gruppen
unterschiedliche Pfade und stellen sich ihre Ergebnisse gegenseitig vor. Die
Aufgaben aller Pfade samt Lösungen findet ihr in den Kapitelseiten. Der
Fortschritt wird nur im jeweiligen Browser gespeichert, nicht zentral.

**Einzelne Kapitel als Baustein.** Jedes Kapitel funktioniert auch für sich,
z. B. Kapitel E in einer Unterrichtsreihe zu industrieller Kommunikation oder
Kapitel H als Einstieg in KI-Agenten.

## Querschnittsmaterial

- **Quiz:** zehn Fragen pro Kapitel mit sofortiger Rückmeldung und Erklärung.
  Gut als Abschluss einer Stunde oder als Hausaufgabe. Die Antworten werden
  nicht gespeichert, das Quiz ist also keine Leistungserhebung.
- **Glossar:** alle Fachbegriffe, in den Kapiteln als Tooltip.
- **[Die Reise eines Messwerts](https://flowthetensor.github.io/Datenkrake/reise-eines-messwerts.html):**
  Vertiefung, die einen Sensorimpuls und eine Akustikmessung durch das ganze
  System verfolgt. Jede Station hat eine „Stolperstelle“ aus dem echten Betrieb.
  Gut für Schülerinnen und Schüler, die den Zusammenhang noch nicht sehen.
- **Digitaler Zwilling:** spielt aufgezeichnete Produktionen ab und ist ohne
  Anlage nutzbar.
- **LangGraph-Werkstatt:** läuft auf jedem Schülerlaptop mit Python
  ([Anleitung](../Agentensystem/langgraph-werkstatt/README.md)).

## Allgemeines Bewertungsraster

Für Erklärungen, Präsentationen und Sprint Reviews in allen Kapiteln. Die
Kapitelseiten nennen jeweils, woran man die Stufen konkret erkennt.

| | 1 · Anfänge | 2 · Grundlegend | 3 · Sicher | 4 · Souverän |
| --- | --- | --- | --- | --- |
| **Fachbegriffe** | werden genannt, aber verwechselt | werden richtig verwendet | werden richtig verwendet und erklärt | werden voneinander abgegrenzt (z. B. MQTT vs. OPC-UA) |
| **Zusammenhang** | einzelne Bausteine isoliert | Reihenfolge der Bausteine stimmt | kann erklären, warum ein Baustein an dieser Stelle sitzt | kann vorhersagen, was passiert, wenn ein Baustein ausfällt |
| **Bezug zur Anlage** | allgemein, ohne Beispiel | mit Beispiel aus der Datenkrake | mit eigenem Beispiel aus der eigenen Station | mit Messwerten oder Daten belegt |
| **Kritische Bewertung** | – | nennt einen Nachteil | wägt Vor- und Nachteile ab | schlägt begründet eine Verbesserung vor |

Für das agile Arbeiten (Kapitel A) kommt die Bewertung der Teamarbeit über
Forgejo dazu: Issues, Kommentare als Lernjournal und das Sprint Review, siehe
[Kapitel A](kapitel-a-agiles-arbeiten.md#bewertung).

## Entstehung mit KI-Unterstützung

Diese Handreichung wurde, wie große Teile des Projekts, **mit Unterstützung
eines KI-Assistenten** (Claude von Anthropic) erstellt. Die Lehrkraft hat sie
fachlich geprüft und verantwortet sie. Lernziele, Zeitangaben und
Musterlösungen sind Vorschläge. Bitte vor dem Einsatz mit Blick auf die eigene
Klasse und den eigenen Lehrplan durchsehen. Mehr dazu im
[Haupt-README](../README.md#hinweis-zur-entstehung-einsatz-von-ki).

## Lizenz

Wie das ganze Projekt unter [CC BY 4.0](../LICENSE-CC-BY): verwenden,
anpassen und weitergeben erlaubt, mit Quellenangabe.
