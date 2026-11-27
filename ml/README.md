# ml/ — Pronóstico de demanda (TCN)

Responsable: Victor Cruz (Developer Backend e IA). Evaluación independiente: Luciana Choquehuanca.

| Archivo | Contenido | EDT |
|---|---|---|
| `originlink_ml/data.py` | Carga del historial, agregación semanal, ventanas y partición temporal | 1.5.1.2 |
| `originlink_ml/tcn.py` | Red Neuronal Convolucional Temporal (convoluciones causales dilatadas) | 1.5.2.1 |
| `originlink_ml/baseline.py` | Promedio móvil de 4 semanas (referencia y respaldo) y MAPE | 1.5.2.2 |
| `originlink_ml/global_model.py` | Modelo TCN **global** (4 tostadores), calendario cíclico, origen rodante a 1 y 4 semanas, elección de método por tostador (ADR-0003) | 1.5.2.1, 1.5.2.3 |
| `train_global.py` | **HU-19**: entrena el modelo global, compara con el promedio móvil y genera `informes/hu19-informe.md` | 1.5.2.3 |
| `train.py` | Entrena, compara TCN vs promedio móvil y guarda `models/tcn.pt` | 1.5.2.3 |
| `generar_datos.py` | Datos sintéticos (plan de contingencia H06a): serie de consumo y datos coherentes para la app. Ver [`datos_sinteticos/README.md`](datos_sinteticos/README.md) | 1.5.1 |

## Uso

```bash
cd ml
python -m venv .venv && .venv\Scripts\activate      # Windows (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python generar_datos.py --maestros-demo              # genera datos_sinteticos/generados/
python train_global.py --csv datos_sinteticos/generados/consumo_semanal_completo.csv      # HU-19 (prueba = 6 semanas, Charter M4)
python train_global.py --csv datos_sinteticos/generados/consumo_semanal_completo.csv --semanas-prueba 12   # sensibilidad
python train.py --csv datos_sinteticos/generados/consumo_semanal_completo.csv --tostador T01 --semanas-prueba 12   # línea base por tostador
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
