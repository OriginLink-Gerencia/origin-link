# HU-19: evaluación de la TCN frente al promedio móvil de 4 semanas

## Protocolo

- Datos: `consumo_semanal_completo.csv`, 4 tostadores, 104–104 semanas cada uno (datos sintéticos, plan de contingencia H06a).
- Partición temporal por tostador: entrenamiento = todo menos las últimas 24 semanas;
  validación = 12 semanas; **prueba = últimas 12 semanas**, apartadas antes de entrenar.
- Modelo: una TCN **global** (convoluciones causales dilatadas, canales [16, 16, 16]), ventana de 12 semanas,
  pronóstico directo de 4 semanas, series normalizadas por tostador con estadísticas del tramo de entrenamiento,
  mes del año (seno/coseno) como entrada, pérdida L1,
  conjunto de 5 redes con distinta inicialización y parada temprana por pérdida de validación.
- Evaluación con **origen rodante**: en cada semana de la región evaluada se pronostica con la historia observada hasta ese momento.
  "1 semana" es el primer paso; "4 semanas" reúne los 4 pasos de cada origen cuyo horizonte completo cae dentro de la región.
- Referencia: promedio móvil de 4 semanas sobre exactamente las mismas semanas.
- Elección de la configuración (calendario, pérdida): solo con el MAPE de validación, nunca con el de prueba.

## Resultados en el conjunto de prueba (12 semanas por tostador)

| Tostador | MAPE TCN 1 sem | MAPE PM 1 sem | MAPE TCN 4 sem | MAPE PM 4 sem | n (1 sem / 4 sem) |
|---|---|---|---|---|---|
| T01 | 10.19 % | 9.51 % | 12.23 % | 14.85 % | 12 / 36 |
| T02 | 12.04 % | 13.58 % | 13.06 % | 16.56 % | 12 / 36 |
| T03 | 6.51 % | 5.67 % | 6.73 % | 6.88 % | 12 / 36 |
| T04 | 6.98 % | 7.39 % | 7.10 % | 8.09 % | 12 / 36 |
| GLOBAL | 8.93 % | 9.04 % | 9.78 % | 11.59 % | 48 / 144 |

## Resultados en validación (usados para elegir el método por tostador)

| Tostador | MAPE TCN 1 sem | MAPE PM 1 sem | MAPE TCN 4 sem | MAPE PM 4 sem | n (1 sem / 4 sem) |
|---|---|---|---|---|---|
| T01 | 3.44 % | 4.16 % | 3.39 % | 4.22 % | 12 / 36 |
| T02 | 11.42 % | 13.08 % | 10.16 % | 13.52 % | 12 / 36 |
| T03 | 4.40 % | 7.11 % | 4.90 % | 7.98 % | 12 / 36 |
| T04 | 14.04 % | 15.73 % | 14.68 % | 17.84 % | 12 / 36 |
| GLOBAL | 8.33 % | 10.02 % | 8.28 % | 10.89 % | 48 / 144 |

## Veredicto

- **OE3-I1 (MAPE de la TCN ≤ 25 %):** cumple (1 semana 8.93 %, 4 semanas 9.78 %).
- **OE4-I3 (TCN mejor que el promedio móvil), a 4 semanas** (horizonte de la recomendación): cumple (9.78 % frente a 11.59 %).
- **OE4-I3 a 1 semana:** EMPATE TÉCNICO (8.93 % frente a 9.04 %; diferencia < 0.5 pp).
- **Método que usará el sistema por tostador (ADR-0003, decidido con la validación):** T01 → TCN, T02 → TCN, T03 → TCN, T04 → TCN.

## Limitaciones

- Los datos son simulados con supuestos documentados; el desempeño con historiales reales puede ser distinto.
- La prueba es corta (12 semanas por tostador): a 4 semanas hay pocos orígenes completos por tostador, así que las
  diferencias pequeñas entre métodos no son concluyentes. Conviene repetir con `--semanas-prueba 12` como análisis de sensibilidad.
- La elección de método por tostador es inestable en los casos límite (p. ej. T02 pasa de promedio móvil a TCN al cambiar el tamaño de la prueba): conviene reevaluarla cuando haya datos reales.
- La validación se usó para elegir la configuración y el método por tostador; por eso su MAPE es algo optimista y no se informa como resultado final.
