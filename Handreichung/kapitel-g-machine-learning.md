# Kapitel G · Machine Learning

[← Übersicht](README.md)

## Worum es geht

Aus den Akustikdaten soll ein **Anomalie-Detektor** entstehen. Die Schüler
vergleichen klassische ML-Verfahren an den eigenen Daten und lernen, wie der
**Anomalie-Poller** heute entscheidet: mit einer einfachen statistischen Regel
oder optional mit einem selbst trainierten Isolation Forest. Der Poller ist die
Brücke zum Agentensystem in Kapitel H.

## Lernziele

Die Schülerinnen und Schüler können …

- Klassifikation, Regression und Anomalie-Erkennung unterscheiden,
- Features und Labels in den Akustikdaten benennen,
- fünf Verfahren (lineare und logistische Regression, Entscheidungsbaum, Naiver Bayes, kNN) nach Vor- und Nachteilen für die eigene Datenlage bewerten,
- die Entscheidungsregel des Anomalie-Pollers erklären und ihre Schwächen benennen,
- erklären, warum man Modelle mit Daten prüft, die sie beim Training nicht gesehen haben.

## Voraussetzungen

Ausbaustufe 1 für die Theorie und das LSTM-Training mit synthetischen Daten.
Für eigene Akustikdaten Ausbaustufe 2. Zum Auswerten Python mit pandas und
scikit-learn oder Jupyter.

## Zeitbedarf und Ablauf

3–4 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 20 min | „Reise einer Akustikmessung“: vom Schall zur Zahl |
| Daten | 40 min | Akustikdaten aufnehmen und labeln (gut/schlecht), CSV herunterladen und sichten |
| Verfahren | 2 × 45 min | Arbeitsauftrag „Verfahren vergleichen“ in Gruppen, je Gruppe ein bis zwei Verfahren |
| Präsentation | 30 min | Gruppen stellen vor: Wann taugt unser Verfahren, wann nicht? |
| Poller | 30 min | Entscheidungsregel des Pollers, Aufgabe „Taugt die Regel?“ |
| Sicherung | 15 min | Quiz Kapitel G |

## Aufgaben und Musterlösungen

### Lernpfad „Datenanalyst“, Schritt 3: Vom Schall zur Zahl

> Wie viele Zahlen pro Sekunde kommen am Mikrofon an, und wie viele bleiben am Ende übrig?

**Musterlösung:**

| Stufe | Datenmenge |
| --- | --- |
| Mikrofon | **16 000** Abtastwerte pro Sekunde |
| FFT auf dem Arduino | Blöcke zu 2048 Werten, daraus je **641** Frequenzwerte (0–5000 Hz) |
| MQTT, Datenbank | **1** Messung pro Sekunde: 641 Spektralwerte plus `peak_freq` und `peak_db` |
| Anomalie-Poller | betrachtet nur **eine** Zahl pro Messung: `peak_db` |

Am Ende entscheidet also eine einzige Zahl. **Stufe 4:** Das ist schnell und
einfach, wirft aber fast alle Information weg. Eine Veränderung, die sich nur in
anderen Frequenzen zeigt, bemerkt der Poller nicht.

### Lernpfad „Datenanalyst“, Schritt 5: Verfahren vergleichen

> Bearbeitet den Arbeitsauftrag zum Vergleich der ML-Verfahren.

Der Arbeitsauftrag im Kapitel lautet: *Vergleicht die Verfahren auf unseren
Akustikdaten (z. B. FFT-Bänder, peak_db, Label gut/schlecht). Begründet pro
Verfahren, wann es für unsere Datenlage sinnvoll ist und wann nicht.*

**Erwartungshorizont:**

| Verfahren | Passt zu unseren Daten, weil … | Passt weniger, weil … |
| --- | --- | --- |
| **Lineare Regression** | sie gut eine Zahl vorhersagen kann, z. B. den Verlauf von `peak_db` über die Zeit (Verschleiß-Trend) | sie für die Frage gut/schlecht nicht gedacht ist: Das Ziel ist eine Klasse, keine Zahl |
| **Logistische Regression** | sie eine gute erste Lösung (Baseline) für gut/schlecht ist und eine Wahrscheinlichkeit liefert | sie nur eine gerade Trennlinie kennt. Ist „schlecht“ manchmal lauter, manchmal leiser als „gut“, scheitert sie |
| **Entscheidungsbaum** | er lesbare Regeln liefert, z. B. „peak_db > -18 → schlecht“, die man mit der Anlage vergleichen kann | er bei wenigen Daten und 641 Spektralwerten schnell auswendig lernt (Overfitting) |
| **Naiver Bayes** | er schnell ist und mit wenig Daten auskommt | benachbarte Frequenzbänder stark zusammenhängen, er aber annimmt, alle Merkmale seien unabhängig |
| **kNN** | er ohne Training auskommt und bei wenigen, gut gelabelten Daten ordentlich arbeitet | Hz und dB ganz andere Größenordnungen haben (vorher skalieren!) und Abstände bei 641 Dimensionen wenig aussagen |

**Was gute Gruppen außerdem bemerken:**

- **Schlechte Beispiele sind selten.** Eine intakte Anlage liefert fast nur
  „gut“. Klassifikatoren brauchen aber Beispiele beider Klassen. Hier passt die
  **Anomalie-Erkennung** besser: Der Isolation Forest in
  `Agentensystem/ml_training/` lernt nur aus „gut“ und meldet alles, was davon
  abweicht.
- **Prüfen mit fremden Daten.** Ein Modell auf denselben Daten zu testen, mit
  denen es trainiert wurde, sagt nichts aus. Also die Daten aufteilen, z. B.
  80 % Training und 20 % Test.
- **Weniger Merkmale.** Statt 641 Einzelwerten kann man Frequenzbänder
  zusammenfassen. Das hilft gegen Overfitting.

### Lernpfad „Datenanalyst“, Schritt 6: Taugt die Regel?

> Denkt euch zwei Situationen aus, in denen der Poller falschen Alarm gibt, und eine, die er übersieht.

**Die Regel:** Alle 15 Sekunden vergleicht der Poller die neueste Messung mit
den 19 vorherigen. Weicht `peak_db` um mehr als das 2,5-Fache der
Standardabweichung vom Mittelwert ab, gilt die Messung als auffällig.

**Mögliche Lösungen:**

*Falscher Alarm:*
- Eine Tür knallt, jemand spricht laut oder ein Handy klingelt neben dem Mikrofon.
- Die Anlage wechselt in einen anderen, normalen Betriebszustand, z. B. wenn ein
  zusätzlicher Motor anläuft.
- Nach einer langen ruhigen Phase ist die Standardabweichung winzig. Dann reicht
  schon eine kleine, harmlose Schwankung.

*Übersehen:*
- **Schleichender Verschleiß.** Das Vergleichsfenster wandert mit. Wird die
  Anlage langsam lauter, verschiebt sich der Mittelwert mit, und die Regel schlägt nie an.
- **Veränderung in einer anderen Frequenz.** Ein neues Pfeifen bei gleichem
  Spitzenpegel ändert `peak_db` nicht.
- **Schon die Referenz ist gestört.** Waren die 19 Vergleichsmessungen bereits
  auffällig, ist die neue Messung „normal“.

Die Aufgabe passt zur **Evaluation-Phase** von CRISP-DM (Kapitel B).

## Typische Schwierigkeiten

- **Zu wenige Daten.** Für einen Vergleich lohnen sich einige hundert gelabelte
  Messungen. Vorher genug Aufnahmezeit einplanen.
- **Labels gemischt.** Wird während der Aufnahme das Label vergessen
  umzustellen, sind die Daten unbrauchbar. Pro Aufnahme festlegen, wer labelt.
- **„Das Modell hat 100 % Genauigkeit.“** Fast immer auf den Trainingsdaten
  gemessen, oder es gibt nur eine Klasse.
- **Poller schlägt nie an.** Er braucht mindestens 6 Messungen. Ohne laufende
  Aufnahme kommen keine neuen Daten.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Features und Label werden richtig benannt.
- Stufe 3: Für jedes Verfahren wird ein datenbezogener Vor- und Nachteil genannt.
- Stufe 4: Es wird erkannt, dass Anomalie-Erkennung hier besser passt als Klassifikation, und die Bewertung wird mit Testdaten belegt.

## Material im Repo

- [`Agentensystem/ml_training/`](../Agentensystem/ml_training): Isolation Forest (Akustik) und LSTM (Zykluszeit)
- [`Agentensystem/anomalie_poller/`](../Agentensystem/anomalie_poller): Poller
- [`DataLake/notebooks/`](../DataLake/notebooks): Notebook für Auswertungen
- CSV-Download der Audio- und PLC-Daten in Kapitel G der Hauptseite
- „Reise einer Akustikmessung“
- Quiz Kapitel G auf der Hauptseite
