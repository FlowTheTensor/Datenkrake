"""
Trainiert ein kleines LSTM, das aus den letzten N Zykluszeiten die
naechste vorhersagt - vorausschauende Instandhaltung: eine Station,
deren tatsaechliche Zykluszeit deutlich von der Vorhersage abweicht,
koennte beginnenden Verschleiss zeigen.

WICHTIG (Stand dieser Version): Die reale OPC-UA-Anbindung der
Zykluszeiten in die MariaDB (Tabelle 'raw_signals', siehe
UAExpertExport/SQL_Schema_Datenkrake.sql) ist noch nicht produktiv (siehe
todo.md, "opc-ua overlay ueberarbeiten"). Dieses Skript versucht daher
zuerst, echte Daten aus 'raw_signals' zu laden - findet es zu wenige,
erzeugt es stattdessen einen klar gekennzeichneten SYNTHETISCHEN
Demo-Datensatz (Sinus-Grundschwankung + Rauschen + langsame Drift als
Verschleiss-Simulation), damit ihr das Training auch ohne laufende
Modellanlage ausprobieren koennt.

Ausfuehren (aus Agentensystem/):
    pip install -r ml_training/requirements.txt
    python -m ml_training.train_lstm_durchlaufzeit
"""
import json
import os
import random

import numpy as np
import pymysql
import torch
import torch.nn as nn

from ml_training.lstm_modell import DurchlaufzeitLSTM

MODELLE_ORDNER = os.path.join(os.path.dirname(__file__), "models")
MODELL_PFAD = os.path.join(MODELLE_ORDNER, "lstm_durchlaufzeit.pt")
META_PFAD = os.path.join(MODELLE_ORDNER, "lstm_durchlaufzeit_meta.json")

FENSTER = 10
HIDDEN_SIZE = 16
EPOCHEN = 60
LERNRATE = 0.01
MIN_REALE_WERTE = 200


def lade_reale_zykluszeiten() -> list[float] | None:
    """Versucht, echte Zykluszeiten aus raw_signals zu laden. Gibt None
    zurueck, wenn die Tabelle fehlt oder zu wenige Werte enthaelt -
    aktueller Stand: diese Tabelle wird von der Datenkrake noch nicht
    produktiv befuellt (siehe Moduldocstring)."""
    host = os.environ.get("DK_DB_HOST", "datenkrake.local")
    port = int(os.environ.get("DK_DB_PORT", "3306"))
    name = os.environ.get("DK_DB_NAME", "telemetry")
    user = os.environ.get("DK_READ_USER", "mcp_read")
    password = os.environ.get("DK_READ_PASSWORD", "changeMeMcp")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=name,
            connect_timeout=5,
        )
    except Exception as e:
        print(f"Keine Verbindung zur MariaDB ({e}) - nutze synthetische Demodaten.")
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT value_numeric FROM raw_signals "
                "WHERE signal_name = 'Zykluszeit' ORDER BY recorded_at"
            )
            werte = [row[0] for row in cur.fetchall() if row[0] is not None]
    except Exception as e:
        print(f"'raw_signals' nicht verfuegbar ({e}) - nutze synthetische Demodaten.")
        return None
    finally:
        conn.close()

    if len(werte) < MIN_REALE_WERTE:
        print(
            f"Nur {len(werte)} reale Zykluszeit-Werte gefunden (< {MIN_REALE_WERTE}) - "
            "nutze synthetische Demodaten."
        )
        return None

    print(f"{len(werte)} reale Zykluszeit-Werte aus raw_signals geladen.")
    return werte


def erzeuge_demo_zykluszeiten(anzahl: int = 1000) -> list[float]:
    """Synthetischer Ersatz fuer echte Zykluszeiten: eine Grund-Zykluszeit
    von 12s mit leichter periodischer Schwankung, Messrauschen und einer
    langsamen Drift nach oben in der zweiten Haelfte (simulierter
    beginnender Verschleiss - genau das soll das LSTM als Abweichung von
    der Vorhersage erkennbar machen)."""
    random.seed(42)
    werte = []
    grundzeit = 12.0
    for i in range(anzahl):
        schwankung = 0.3 * np.sin(i / 15.0)
        rauschen = random.gauss(0, 0.15)
        drift = 0.004 * max(0, i - anzahl // 2)  # Verschleiss-Simulation
        werte.append(grundzeit + schwankung + rauschen + drift)
    print(f"{anzahl} synthetische Demo-Zykluszeiten erzeugt (Drift ab Index {anzahl // 2}).")
    return werte


def erzeuge_trainingsdaten(werte: list[float], fenster: int, mittel: float, std: float):
    normiert = [(w - mittel) / std for w in werte]
    X, y = [], []
    for i in range(len(normiert) - fenster):
        X.append(normiert[i : i + fenster])
        y.append(normiert[i + fenster])
    X = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)  # (n, fenster, 1)
    y = torch.tensor(y, dtype=torch.float32)
    return X, y


def main() -> None:
    os.makedirs(MODELLE_ORDNER, exist_ok=True)

    werte = lade_reale_zykluszeiten() or erzeuge_demo_zykluszeiten()

    mittel = float(np.mean(werte))
    std = float(np.std(werte)) or 0.01

    X, y = erzeuge_trainingsdaten(werte, FENSTER, mittel, std)
    grenze = int(len(X) * 0.85)
    X_train, y_train = X[:grenze], y[:grenze]
    X_val, y_val = X[grenze:], y[grenze:]

    modell = DurchlaufzeitLSTM(hidden_size=HIDDEN_SIZE)
    optimierer = torch.optim.Adam(modell.parameters(), lr=LERNRATE)
    verlustfunktion = nn.MSELoss()

    for epoche in range(1, EPOCHEN + 1):
        modell.train()
        optimierer.zero_grad()
        vorhersage = modell(X_train)
        verlust = verlustfunktion(vorhersage, y_train)
        verlust.backward()
        optimierer.step()

        if epoche % 10 == 0 or epoche == EPOCHEN:
            modell.eval()
            with torch.no_grad():
                val_verlust = (
                    verlustfunktion(modell(X_val), y_val).item() if len(X_val) else float("nan")
                )
            print(
                f"Epoche {epoche:3d}: Trainingsverlust {verlust.item():.4f}, "
                f"Validierungsverlust {val_verlust:.4f}"
            )

    torch.save(modell.state_dict(), MODELL_PFAD)
    with open(META_PFAD, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fenster": FENSTER,
                "hidden_size": HIDDEN_SIZE,
                "mittel": mittel,
                "std": std,
                "schwelle_faktor": 3.0,
            },
            f,
            indent=2,
        )

    print(f"Modell gespeichert unter {MODELL_PFAD}")
    print(f"Metadaten gespeichert unter {META_PFAD}")


if __name__ == "__main__":
    main()
