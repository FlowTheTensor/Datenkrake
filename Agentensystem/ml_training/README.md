<img align="right" src="../../Images/krake_klein.jpg" alt="Datenkrake Logo" width="120">

# ML-Training für vorausschauende Instandhaltung

Zwei eigenständige Trainingsskripte, die Schüler selbst ausführen – kein
automatisches Retraining, keine MLOps-Pipeline. Ergebnis: Dateien in
`models/`, die die Agenten (aktuell: `anomalie_poller`) optional statt der
festen Heuristik nutzen.

## 1. Isolation Forest (Akustik)

`train_isolation_forest_akustik.py` lädt echte Messungen aus
`audio_spectrum` (Merkmale: `peak_freq`, `peak_db`), trainiert auf den
mit `gut` gelabelten Messungen und speichert das Modell als
`models/isolation_forest_akustik.joblib`.

Danach im Agentensystem `.env` aktivieren:

```dotenv
ANOMALIE_METHODE=isolation_forest
```

Der `anomalie_poller` nutzt das Modell automatisch, sobald es existiert –
ohne trainiertes Modell fällt er auf `ANOMALIE_METHODE=zscore` zurück.

## 2. LSTM (Durchlaufzeit/Zykluszeit)

`train_lstm_durchlaufzeit.py` sagt aus den letzten `fenster` Zykluszeiten
den nächsten Wert voraus – weicht die tatsächliche Zykluszeit stark von
der Vorhersage ab, ist das ein möglicher Hinweis auf beginnenden
Verschleiß (vorausschauende Instandhaltung).

**Wichtig:** die reale OPC-UA-Anbindung der Zykluszeiten in die MariaDB
(`raw_signals`, siehe `UAExpertExport/SQL_Schema_Datenkrake.sql`) ist noch
nicht produktiv (siehe `todo.md`, "opc-ua overlay überarbeiten"). Das
Skript versucht zuerst, echte Daten zu laden, erzeugt bei zu wenigen
Zeilen automatisch einen klar gekennzeichneten synthetischen
Demo-Datensatz (Grund-Zykluszeit + Rauschen + simulierte Verschleiß-Drift)
– so lässt sich das Training schon jetzt ausprobieren.

`shared/predictive_models.durchlaufzeit_vorhersage()` lädt das Modell zur
Laufzeit; noch ist kein bestehender Agent fest damit verdrahtet (das
folgt, sobald reale Zykluszeit-Daten fließen).

## Setup

```bash
cd Agentensystem
pip install -r ml_training/requirements.txt
python -m ml_training.train_isolation_forest_akustik
python -m ml_training.train_lstm_durchlaufzeit
```

`models/` ist nicht versioniert (siehe `.gitignore`) – jede Schülerin/jeder
Schüler trainiert ihre/seine eigenen Modelldateien lokal.

## Bekannte Vereinfachungen

- Kein automatisches Retraining und kein Modell-Versionsstand – wer ein
  neues Modell will, führt das Skript erneut aus und überschreibt die Datei.
- Die Isolation-Forest-Merkmale sind bewusst auf `peak_freq`/`peak_db`
  beschränkt (kein FFT-Array als Feature), damit das Modell nachvollziehbar
  bleibt.
- Das LSTM nutzt aktuell synthetische Demodaten (siehe oben) – die
  Verschleiß-Drift ist eine Simulation, keine reale Beobachtung.
