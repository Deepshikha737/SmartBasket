"""
Lightweight sequence model for next-step price forecasting.

Training on real series is a separate offline job; at runtime we combine
the model forward pass with recent price history from MongoDB.
"""

import logging
from pathlib import Path
from threading import Lock
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

_log = logging.getLogger(__name__)
_lock = Lock()
_model: Optional["PriceLSTM"] = None
_state_path = Path("data/price_lstm.pt")


class PriceLSTM(nn.Module):
    def __init__(self, input_size: int = 1, hidden: int = 32, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def get_price_model(device: str = "cpu") -> PriceLSTM:
    global _model
    with _lock:
        if _model is None:
            m = PriceLSTM()
            if _state_path.exists():
                m.load_state_dict(torch.load(_state_path, map_location=device, weights_only=True))
                _log.info("Loaded LSTM weights from %s", _state_path)
            else:
                torch.manual_seed(42)
                for p in m.parameters():
                    nn.init.xavier_uniform_(p) if p.dim() > 1 else nn.init.zeros_(p)
                _log.warning("No LSTM checkpoint at %s — using initialized weights (demo).", _state_path)
            m.eval()
            _model = m
        return _model


def predict_next_price(series: list[float], window: int = 8) -> float:
    """series: oldest -> newest prices."""
    if not series:
        return 0.0
    model = get_price_model()
    seq = np.array(series[-window:], dtype=np.float32).reshape(1, -1, 1)
    if seq.shape[1] < 2:
        return float(series[-1])
    x = torch.from_numpy(seq)
    with torch.no_grad():
        y = model(x)
    return float(max(0.0, y.item()))
