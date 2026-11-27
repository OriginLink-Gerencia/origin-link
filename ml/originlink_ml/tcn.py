"""Red Neuronal Convolucional Temporal (TCN) para pronosticar el consumo semanal de café verde.

Arquitectura (Bai, Kolter y Koltun, 2018): bloques residuales de convoluciones 1D causales y dilatadas.
- Causal: la predicción de la semana t solo usa semanas <= t (no "ve el futuro").
- Dilatada: la dilatación crece 1, 2, 4, ... para cubrir muchas semanas con pocas capas.
"""

import torch
from torch import nn


class Chomp1d(nn.Module):
    """Recorta el relleno sobrante del final para que la convolución sea causal."""

    def __init__(self, chomp_size: int):
        super().__init__()
        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x[:, :, : -self.chomp_size] if self.chomp_size > 0 else x


class TemporalBlock(nn.Module):
    def __init__(self, n_in: int, n_out: int, kernel_size: int, dilation: int, dropout: float):
        super().__init__()
        padding = (kernel_size - 1) * dilation
        self.net = nn.Sequential(
            nn.Conv1d(n_in, n_out, kernel_size, padding=padding, dilation=dilation),
            Chomp1d(padding),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Conv1d(n_out, n_out, kernel_size, padding=padding, dilation=dilation),
            Chomp1d(padding),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.downsample = nn.Conv1d(n_in, n_out, 1) if n_in != n_out else None
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(self.net(x) + res)


class TCN(nn.Module):
    """Recibe una ventana de `window` semanas y predice las próximas `horizon` semanas.

    Entrada: (batch, n_features, window). Salida: (batch, horizon).
    """

    def __init__(
        self,
        n_features: int = 1,
        channels: tuple[int, ...] = (16, 16, 16),
        kernel_size: int = 3,
        dropout: float = 0.1,
        horizon: int = 4,
    ):
        super().__init__()
        layers = []
        for i, n_out in enumerate(channels):
            n_in = n_features if i == 0 else channels[i - 1]
            layers.append(TemporalBlock(n_in, n_out, kernel_size, dilation=2**i, dropout=dropout))
        self.tcn = nn.Sequential(*layers)
        self.head = nn.Linear(channels[-1], horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.tcn(x)  # (batch, canales, window)
        return self.head(h[:, :, -1])  # usa el último paso temporal


def receptive_field(kernel_size: int, n_layers: int) -> int:
    """Semanas de historia que "ve" la red: 1 + 2*(k-1)*(2^n - 1)."""
    return 1 + 2 * (kernel_size - 1) * (2**n_layers - 1)
