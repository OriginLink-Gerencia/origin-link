# ml/ — Pronóstico de demanda (TCN)

Responsable: Victor Cruz (Developer Backend e IA). Evaluación independiente: Luciana Choquehuanca.

| Archivo | Contenido | EDT |
|---|---|---|
| `originlink_ml/data.py` | Carga del historial, agregación semanal, ventanas y partición temporal | 1.5.1.2 |
| `originlink_ml/tcn.py` | Red Neuronal Convolucional Temporal (convoluciones causales dilatadas) | 1.5.2.1 |
| `originlink_ml/baseline.py` | Promedio móvil de 4 semanas (referencia y respaldo) y MAPE | 1.5.2.2 |
| `train.py` | Entrena, compara TCN vs promedio móvil y guarda `models/tcn.pt` | 1.5.2.3 |

## Uso

```bash
cd ml
python -m venv .venv && .venv\Scripts\activate      # Windows (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python train.py --demo                               # prueba con datos sintéticos
python train.py --csv data/consumo.csv --tostador T01 --semanas-prueba 8
pytest
```

Formato de `data/consumo.csv` (los datos reales **no** se suben al repo):

```
tostador_id,fecha,kg_consumidos
T01,2025-01-06,6.5
```

## Notas

- Entrena en segundos o pocos minutos en CPU: el historial semanal es pequeño.
- El riesgo no es el tiempo de entrenamiento sino la **cantidad de datos**. Si el historial es menor que
  `12 + 4 + semanas de prueba`, el script se detiene y se usa el promedio móvil.
- El conjunto de prueba (últimas N semanas) se fija antes de entrenar y no se usa para ajustar el modelo.
