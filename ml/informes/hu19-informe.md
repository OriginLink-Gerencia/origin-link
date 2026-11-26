# HU-19: evaluación de la TCN frente al promedio móvil de 4 semanas

## Protocolo

- Datos: `consumo_semanal_completo.csv`, 4 tostadores, 104–104 semanas cada uno (datos sintéticos, plan de contingencia H06a).
- Partición temporal por tostador: entrenamiento = todo menos las últimas 18 semanas;
  validación = 12 semanas; **prueba = últimas 6 semanas**, apartadas antes de entrenar.
- Modelo: una TCN **global** (convoluciones causales dilatadas, canales [16, 16, 16]), ventana de 12 semanas,
  pronóstico directo de 4 semanas, series normalizadas por tostador con estadísticas del tramo de entrenamiento,
  mes del año (seno/coseno) como entrada, pérdida L1,
  conjunto de 5 redes con distinta inicialización y parada temprana por pérdida de validación.
- Evaluación con **origen rodante**: en cada semana de la región evaluada se pronostica con la historia observada hasta ese momento.
  "1 semana" es el primer paso; "4 semanas" reúne los 4 pasos de cada origen cuyo horizonte completo cae dentro de la región.
- Referencia: promedio móvil de 4 semanas sobre exactamente las mismas semanas.
- Elección de la configuración (calendario, pérdida): solo con el MAPE de validación, nunca con el de prueba.

## Resultados en el conjunto de prueba (6 semanas por tostador)

| Tostador | MAPE TCN 1 sem | MAPE PM 1 sem | MAPE TCN 4 sem | MAPE PM 4 sem | n (1 sem / 4 sem) |
|---|---|---|---|---|---|
| T01 | 9.76 % | 7.81 % | 8.55 % | 9.65 % | 6 / 12 |
| T02 | 10.13 % | 9.72 % | 9.43 % | 15.07 % | 6 / 12 |
| T03 | 3.21 % | 6.42 % | 3.84 % | 8.63 % | 6 / 12 |
| T04 | 12.30 % | 11.50 % | 14.20 % | 16.15 % | 6 / 12 |
| GLOBAL | 8.85 % | 8.86 % | 9.00 % | 12.37 % | 24 / 48 |

## Resultados en validación (usados para elegir el método por tostador)

| Tostador | MAPE TCN 1 sem | MAPE PM 1 sem | MAPE TCN 4 sem | MAPE PM 4 sem | n (1 sem / 4 sem) |
|---|---|---|---|---|---|
| T01 | 6.43 % | 8.00 % | 6.26 % | 9.73 % | 12 / 36 |
| T02 | 11.62 % | 13.34 % | 16.68 % | 14.25 % | 12 / 36 |
| T03 | 6.92 % | 6.03 % | 6.64 % | 7.38 % | 12 / 36 |
| T04 | 6.89 % | 10.59 % | 7.21 % | 13.77 % | 12 / 36 |
| GLOBAL | 7.96 % | 9.49 % | 9.20 % | 11.28 % | 48 / 144 |

## Veredicto

- **OE3-I1 (MAPE de la TCN ≤ 25 %):** cumple (1 semana 8.85 %, 4 semanas 9.00 %).
- **OE4-I3 (TCN mejor que el promedio móvil), a 4 semanas** (horizonte de la recomendación): cumple (9.00 % frente a 12.37 %).
- **OE4-I3 a 1 semana:** EMPATE TÉCNICO (8.85 % frente a 8.86 %; diferencia < 0.5 pp).
- **Método que usará el sistema por tostador (ADR-0003, decidido con la validación):** T01 → TCN, T02 → PROMEDIO_MOVIL, T03 → TCN, T04 → TCN.

## Limitaciones

- Los datos son simulados con supuestos documentados; el desempeño con historiales reales puede ser distinto.
- La prueba es corta (6 semanas por tostador): a 4 semanas hay pocos orígenes completos por tostador, así que las
  diferencias pequeñas entre métodos no son concluyentes. Conviene repetir con `--semanas-prueba 12` como análisis de sensibilidad.
- La elección de método por tostador es inestable en los casos límite (p. ej. T02 pasa de promedio móvil a TCN al cambiar el tamaño de la prueba): conviene reevaluarla cuando haya datos reales.
- La validación se usó para elegir la configuración y el método por tostador; por eso su MAPE es algo optimista y no se informa como resultado final.
