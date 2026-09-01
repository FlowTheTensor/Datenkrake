"""
Laedt die von Schuelern selbst trainierten Modelle aus ml_training/models/
und stellt sie den Agenten (aktuell: anomalie_poller) als einfache
Inferenzfunktionen zur Verfuegung. Kennt weder MCP noch A2A noch LAP.

Ohne trainiertes Modell liefern beide Ladefunktionen None zurueck - der
Aufrufer faellt dann automatisch auf die bisherige, feste Heuristik
zurueck (siehe anomalie_poller/poller.py). Damit bleibt das System auch
ohne ML-Training vollstaendig funktionsfaehig.
"""
from pathlib import Path

from shared import db_service

MODELLE_ORDNER = Path(__file__).resolve().parent.parent / "ml_training" / "models"
ISOLATION_FOREST_PFAD = MODELLE_ORDNER / "isolation_forest_akustik.joblib"
LSTM_MODELL_PFAD = MODELLE_ORDNER / "lstm_durchlaufzeit.pt"
LSTM_META_PFAD = MODELLE_ORDNER / "lstm_durchlaufzeit_meta.json"

_isolation_forest_cache = None
_lstm_cache = None  # (modell, meta), einmal geladen dann zwischengespeichert


def lade_isolation_forest():
    """Laedt (und cached) das trainierte Isolation-Forest-Modell. Gibt
    None zurueck, wenn noch nicht trainiert wurde."""
    global _isolation_forest_cache
    if _isolation_forest_cache is not None:
        return _isolation_forest_cache
    if not ISOLATION_FOREST_PFAD.exists():
        return None

    import joblib

    _isolation_forest_cache = joblib.load(ISOLATION_FOREST_PFAD)
    return _isolation_forest_cache


def akustik_anomalie_ml() -> dict | None:
    """Wie db_service.pruefe_akustik_anomalie(), aber mit dem selbst
    trainierten Isolation-Forest-Modell statt der Mittelwert/Std-
    Heuristik. Gibt None zurueck, wenn kein Modell trainiert oder keine
    Messung vorhanden ist - der Aufrufer soll dann auf die Heuristik
    zurueckfallen (siehe anomalie_poller/poller.py)."""
    modell = lade_isolation_forest()
    if modell is None:
        return None

    letzte = db_service.get_letzte_spectrum_messung()
    if not letzte or letzte.get("peak_freq") is None:
        return None

    merkmale = [[letzte["peak_freq"], letzte["peak_db"]]]
    vorhersage = modell.predict(merkmale)[0]  # -1 = Anomalie, 1 = normal
    score = float(modell.score_samples(merkmale)[0])  # je kleiner/negativer, desto anomaler

    return {
        "anomalie": bool(vorhersage == -1),
        "bezug_id": int(letzte["id"]),
        "aktuell_peak_db": letzte["peak_db"],
        # Zweckentfremdet fuer die audio_anomalien-Tabelle (kein Mittelwert/Std-
        # Konzept bei Isolation Forest): referenz_mittel traegt hier den Score.
        "referenz_mittel": round(score, 4),
        "referenz_std": 0.0,
        "methode": "isolation_forest",
    }


def lade_lstm():
    """Laedt (und cached) das trainierte LSTM-Modell samt Metadaten
    (Fenstergroesse, Normalisierung). Gibt None zurueck, wenn noch nicht
    trainiert wurde. Importiert torch erst hier, damit Agenten ohne
    LSTM-Nutzung torch nicht installieren muessen."""
    global _lstm_cache
    if _lstm_cache is not None:
        return _lstm_cache
    if not LSTM_MODELL_PFAD.exists() or not LSTM_META_PFAD.exists():
        return None

    import json

    import torch

    from ml_training.lstm_modell import DurchlaufzeitLSTM

    meta = json.loads(LSTM_META_PFAD.read_text(encoding="utf-8"))
    modell = DurchlaufzeitLSTM(hidden_size=meta["hidden_size"])
    modell.load_state_dict(torch.load(LSTM_MODELL_PFAD, map_location="cpu"))
    modell.eval()

    _lstm_cache = (modell, meta)
    return _lstm_cache


def durchlaufzeit_vorhersage(sequenz: list[float]) -> dict | None:
    """Sagt den naechsten Durchlaufzeit-/Zykluszeit-Wert anhand der
    letzten N Werte voraus (N = meta['fenster']) und meldet eine
    Auffaelligkeit, wenn der zuletzt BEOBACHTETE Wert deutlich von der
    Vorhersage abweicht. Gibt None zurueck, wenn kein Modell trainiert
    wurde oder zu wenige Werte uebergeben wurden."""
    geladen = lade_lstm()
    if geladen is None:
        return None
    modell, meta = geladen

    fenster = meta["fenster"]
    if len(sequenz) < fenster + 1:
        return None

    import torch

    mittel, std = meta["mittel"], meta["std"]
    eingabe = sequenz[-(fenster + 1) : -1]
    tatsaechlich = sequenz[-1]

    normiert = [(w - mittel) / std for w in eingabe]
    x = torch.tensor(normiert, dtype=torch.float32).reshape(1, fenster, 1)
    with torch.no_grad():
        vorhersage_norm = modell(x).item()
    vorhersage = vorhersage_norm * std + mittel

    abweichung = abs(tatsaechlich - vorhersage)
    schwelle = meta.get("schwelle_faktor", 3.0) * std

    return {
        "auffaellig": abweichung > schwelle,
        "vorhersage": round(vorhersage, 3),
        "tatsaechlich": round(tatsaechlich, 3),
        "abweichung": round(abweichung, 3),
        "methode": "lstm",
    }
