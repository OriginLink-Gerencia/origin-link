import numpy as np
import torch

from originlink_ml.baseline import mape, promedio_movil
from originlink_ml.tcn import TCN


def test_promedio_movil_usa_ultimas_4_semanas():
    assert promedio_movil(np.array([1, 2, 3, 4, 5, 6, 7, 8]), ventana=4, horizon=2).tolist() == [6.5, 6.5]


def test_mape_ignora_semanas_con_cero():
    assert abs(mape([10, 0, 20], [11, 5, 18]) - 10.0) < 1e-9


def test_tcn_devuelve_horizonte_esperado():
    modelo = TCN(n_features=1, horizon=4)
    salida = modelo(torch.randn(2, 1, 12))
    assert salida.shape == (2, 4)


def test_tcn_es_causal():
    """Cambiar la última semana no debe alterar las salidas internas de semanas anteriores."""
    torch.manual_seed(0)
    modelo = TCN(n_features=1, horizon=1, dropout=0.0).eval()
    x = torch.randn(1, 1, 12)
    x2 = x.clone()
    x2[0, 0, -1] += 10
    with torch.no_grad():
        assert torch.allclose(modelo.tcn(x)[:, :, :-1], modelo.tcn(x2)[:, :, :-1])
