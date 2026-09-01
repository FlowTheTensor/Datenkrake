"""
Architektur des LSTM-Modells fuer die Durchlaufzeit-Vorhersage. Ausgelagert
in ein eigenes Modul, damit Training (train_lstm_durchlaufzeit.py) und
Inferenz (shared/predictive_models.py) exakt dieselbe Modellklasse nutzen -
sonst schlaegt load_state_dict() beim Laden fehl.
"""
import torch
import torch.nn as nn


class DurchlaufzeitLSTM(nn.Module):
    def __init__(self, hidden_size: int = 16, num_layers: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1, hidden_size=hidden_size, num_layers=num_layers, batch_first=True
        )
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, fenster, 1) -> letzter Zeitschritt des LSTM-Ausgangs
        out, _ = self.lstm(x)
        letzter_schritt = out[:, -1, :]
        return self.head(letzter_schritt).squeeze(-1)
