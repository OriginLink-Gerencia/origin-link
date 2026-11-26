"""Carga opcional del modelo TCN global entrenado en ml/ (HU-19).

El backend funciona sin él: si falta el archivo, PyTorch o el paquete `originlink_ml`, `cargar_modelo()` devuelve
None y el pronóstico usa el promedio móvil de 4 semanas (ADR-0003). Para que la API use la TCN hay que instalar
`requirements-ml.txt` y entrenar con `ml/train_global.py`.
"""

import datetime as dt
import logging
import sys
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings

log = logging.getLogger(__name__)


class ModeloTCN:
    """Conjunto de redes entrenadas. `pronosticar` devuelve las 4 semanas siguientes a la última de la serie."""

    def __init__(self, modelos, cfg, global_model):
        self._modelos, self._cfg, self._gm = modelos, cfg, global_model

    @property
    def minimo_semanas(self) -> int:
        return self._cfg.minimo_semanas

    def pronosticar(self, semanas: list[dt.date], kg: list[float]) -> list[float]:
        import numpy as np
        import pandas as pd

        serie = self._gm.Serie(id="tostador", fechas=pd.DatetimeIndex(semanas), kg=np.asarray(kg, dtype=float))
        return [float(x) for x in self._gm.pronosticar(self._modelos, serie, len(kg), self._cfg)]


def _carpeta_ml() -> Path:
    ajustes = get_settings()
    return Path(ajustes.ml_path) if ajustes.ml_path else Path(__file__).resolve().parents[3] / "ml"


@lru_cache
def cargar_modelo() -> ModeloTCN | None:
    ajustes = get_settings()
    ruta = Path(ajustes.model_path)
    if not ruta.is_absolute():
        ruta = (Path(__file__).resolve().parents[2] / ruta).resolve()
    if not ruta.is_file():
        log.info("No hay modelo TCN en %s: el pronóstico usa el promedio móvil", ruta)
        return None
    try:
        import torch

        carpeta = str(_carpeta_ml())
        if carpeta not in sys.path:
            sys.path.insert(0, carpeta)
        from originlink_ml import global_model as gm

        guardado = torch.load(ruta, map_location="cpu", weights_only=True)
        if not guardado.get("estados"):
            return None  # el entrenamiento no tuvo historiales suficientes y solo guardó el método de respaldo
        cfg = gm.Config(**{k: tuple(v) if isinstance(v, list) else v for k, v in guardado["config"].items()})
        modelos = []
        for estado in guardado["estados"]:
            red = gm.TCNGlobal(cfg)
            red.load_state_dict(estado)
            modelos.append(red.eval())
        return ModeloTCN(modelos, cfg, gm)
    except Exception:
        log.exception("No se pudo cargar el modelo TCN; se usa el promedio móvil")
        return None
