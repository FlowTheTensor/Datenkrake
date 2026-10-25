# Kapitel D · Datenerhebung

[← Übersicht](README.md)

## Worum es geht

Hier entstehen die Rohdaten. Es gibt zwei Quellen: Der **Arduino UNO Q**
zerlegt den Klang der Anlage in ein Frequenzspektrum. Die **SPS-Stationen**
liefern Signale wie Motorlauf und Bandsensoren, die Node-RED per OPC-UA abfragt.
Der **digitale Zwilling** macht die SPS-Daten sichtbar, indem er aufgezeichnete
Produktionen auf dem Anlagenschema abspielt.

## Lernziele

Die Schülerinnen und Schüler können …

- die beiden Datenquellen der Datenkrake und ihre Messgrößen beschreiben,
- aus dem Zwilling den Ablauf einer Station ablesen (Motor, Bandsensoren),
- die Akustik-Kennwerte `peak_freq`, `peak_db` und das Label erklären,
- begründen, warum die Qualität der Datenerhebung die Grenze für alle späteren Auswertungen setzt.

## Voraussetzungen

Ausbaustufe 0 für den Zwilling mit der Demo-Aufzeichnung. Eigene Akustikdaten ab
Stufe 2, eigene SPS-Daten ab Stufe 3.

## Zeitbedarf und Ablauf

2 DS.

| Phase | Dauer | Inhalt |
| --- | --- | --- |
| Einstieg | 15 min | Zwilling gemeinsam abspielen: Was passiert an der Anlage? |
| SPS-Signale | 45 min | Aufgabe „Welche Signale gibt es?“ für die eigene Station |
| Akustik | 45 min | Arduino-Weboberfläche zeigen, Messung mit Label aufnehmen, Kennwerte erklären |
| Vertiefung | 30 min | „Reise eines Messwerts“, Halt 1–3 |
| Sicherung | 15 min | Quiz Kapitel D |

## Aufgaben und Musterlösungen

### Lernpfad „Erster Überblick“, Schritt 4: Die Anlage in Bewegung sehen

> Öffnet den digitalen Zwilling und spielt eine Produktion ab. Beobachtet, in welcher Reihenfolge die Stationen arbeiten.

**Erwartung:** Die Schüler beschreiben den **Materialfluss** über die Stationen.
Laut Anlagenschema verläuft er vom Palettenlager bis zum Abfüllen, mit den
Transfersystemen dazwischen und dem Ast zum Hochregallager. Die genaue
Reihenfolge ergibt sich aus der Aufzeichnung. Am besten spielt man die
Produktion vorher einmal selbst ab und notiert sie als Lösung.

Gute Antworten bemerken außerdem, dass **mehrere Stationen gleichzeitig aktiv**
sein können und dass einzelne Signale scheinbar fehlen (siehe „Typische
Schwierigkeiten“).

### Lernpfad „Automatisierer“, Schritt 2: Welche Signale gibt es?

> Notiert für eure Station, welche Signale (Motor, Bandsensoren) wann aktiv werden.

**Musterlösung (Muster, je Station anzupassen):** Pro Transfersystem-Abschnitt
gibt es vier Signale:

| Signal | Tag (Beispiel) | Bedeutung |
| --- | --- | --- |
| Motor Rechtslauf | `AL_MA1_Rechtslauf` | Band fördert nach rechts |
| Motor Linkslauf | `AL_MA1_Linkslauf` | Band fördert nach links |
| Bandsensor links | `AL_BG1_…` bzw. `sBandSensorLinks` | Werkstückträger steht am linken Ende |
| Bandsensor rechts | `AL_BG2_Bandsensor_Rechts` bzw. `sBandSensorRechts` | Werkstückträger steht am rechten Ende |

Die Namen der Bandsensoren unterscheiden sich je nach Station. Ein schöner
Anlass für die Frage, warum einheitliche Benennung in der Automatisierung wichtig ist.

Typischer Ablauf: Der Motor läuft an, der Werkstückträger fährt los, der
Bandsensor an der Zielseite meldet ihn, und der Motor stoppt. Rechts- und
Linkslauf sind nie gleichzeitig aktiv.

Die genauen Tags der eigenen Station stehen in
[`UAExpertExport/stationen/`](../UAExpertExport/stationen) bzw. in der
OPC-UA-Signaldokumentation der Hauptseite.

### Lernpfad „Datenanalyst“, Schritt 2: Was wird eigentlich gemessen?

> Was bedeuten peak_freq, peak_db und das Label gut/schlecht?

**Musterlösung:**

- **`peak_freq`** ist die Frequenz in Hz, die im aktuellen Klang am lautesten
  ist, also der „Hauptton“.
- **`peak_db`** ist der Pegel dieser Frequenz in dB. Die Werte sind negativ,
  weil sie relativ zum größtmöglichen Pegel angegeben werden: 0 dB wäre das
  Maximum, je negativer, desto leiser.
- Das **Label** `gut`/`schlecht` setzt **ein Mensch** in der Weboberfläche des
  Arduino, bevor er aufnimmt. Es ist die „richtige Antwort“, aus der ein Modell
  später lernt.

Zusätzlich wird das komplette **Spektrum** mit 641 Werten von 0 bis 5000 Hz
gespeichert.

**Stufe 4:** Die Schüler erkennen, dass das Label nur so gut ist wie die Person,
die es setzt. Falsch gelabelte Aufnahmen bringen dem Modell das Falsche bei.

## Typische Schwierigkeiten

- **Im Zwilling fehlen Impulse.** Ein Bandsensor-Impuls ist sehr kurz. Node-RED
  fragt nur einmal pro Sekunde ab und bei vielen Knoten wegen der Drossel sogar
  seltener. Kürzere Impulse werden dann nie gesehen. Das ist kein Fehler im
  Zwilling, sondern eine echte Grenze der Datenerhebung und ein gutes Thema für
  ein Issue. Die robuste Lösung ist ein Flankenzähler in der SPS.
- **Falsche Zeitstempel.** Einige SPS haben eine falsch gestellte Uhr. Deshalb
  setzt Node-RED den Zeitstempel selbst.
- **Die Akustik nimmt nichts auf.** Bei der Dockingstation auf die Reihenfolge
  achten: erst Strom, dann Webcam, zuletzt Arduino. Und die Aufnahme muss in der
  Weboberfläche gestartet sein, sonst sendet der Arduino nichts.
- **Störgeräusche.** Gespräche oder Türen neben dem Mikrofon landen ebenfalls
  in den Daten. Darüber lohnt es sich vor dem Aufnehmen zu sprechen.

## Bewertung

Woran man Verständnis erkennt:

- Stufe 2: Signale und Kennwerte werden richtig benannt.
- Stufe 3: Der Ablauf einer Station wird aus dem Zwilling korrekt beschrieben.
- Stufe 4: Lücken in den Daten werden bemerkt und auf die Abfragerate zurückgeführt.

## Material im Repo

- [`ArduinoUnoQ/`](../ArduinoUnoQ): Audio-Erfassung, FFT, Weboberfläche
- [`UAExpertExport/`](../UAExpertExport): OPC-UA-Knoten aller Stationen
- [`Raspberry/web/anlage-zwilling.html`](../Raspberry/web/anlage-zwilling.html): digitaler Zwilling
- Quiz Kapitel D auf der Hauptseite
