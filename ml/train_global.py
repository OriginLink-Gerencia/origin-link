"""HU-19: entrena la TCN global y la compara con el promedio móvil de 4 semanas.

Uso (desde la carpeta ml/):
    python train_global.py --csv datos_sinteticos/generados/consumo_semanal_completo.csv
    python train_global.py --csv ... --semanas-prueba 12      # sensibilidad con una prueba más larga

Genera:
    models/tcn_global.pt           modelo (conjunto de redes) y método elegido por tostador
    informes/hu19-informe.md       informe con los MAPE, el veredicto de OE3-I1 / OE4-I3 y las limitaciones
    informes/hu19-resultados.json  los mismos números en formato máquina

La configuración (calendario + pérdida L1) se eligió comparando solo el MAPE de VALIDACIÓN; el conjunto de
prueba se fija antes de entrenar y no interviene en ninguna decisión.
"""

import argparse
import json
from dataclasses import replace
from pathlib import Path

import torch

from originlink_ml.global_model import (
    PM_METODO,
    TCN_METODO,
    Config,
    cargar_series,
    config_a_dict,
    elegir_metodo_por_tostador,
    entrenar_conjunto,
    errores,
    resumen_mape,
)

META_MAPE = 25.0  # OE3-I1


def tabla_md(res) -> str:
    filas = ["| Tostador | MAPE TCN 1 sem | MAPE PM 1 sem | MAPE TCN 4 sem | MAPE PM 4 sem | n (1 sem / 4 sem) |",
             "|---|---|---|---|---|---|"]
    for tid, r in res.iterrows():
        filas.append(
            f"| {tid} | {r.mape_tcn_1s:.2f} % | {r.mape_pm_1s:.2f} % | {r.mape_tcn_4s:.2f} % | "
            f"{r.mape_pm_4s:.2f} % | {int(r.n_1s)} / {int(r.n_4s)} |"
        )
    return "\n".join(filas)


def comparar(tcn: float, pm: float, margen: float = 0.5) -> str:
    """OE4-I3 con un margen: una diferencia menor a `margen` puntos porcentuales es un empate técnico."""
    if abs(tcn - pm) < margen:
        return f"EMPATE TÉCNICO ({tcn:.2f} % frente a {pm:.2f} %; diferencia < {margen} pp)"
    return f"{'cumple' if tcn < pm else 'NO cumple'} ({tcn:.2f} % frente a {pm:.2f} %)"


def veredicto(res, metodos: dict[str, str]) -> list[str]:
    g = res.loc["GLOBAL"]
    cumple_i1 = g.mape_tcn_1s <= META_MAPE and g.mape_tcn_4s <= META_MAPE
    return [
        f"- **OE3-I1 (MAPE de la TCN ≤ {META_MAPE:.0f} %):** {'cumple' if cumple_i1 else 'NO cumple'} "
        f"(1 semana {g.mape_tcn_1s:.2f} %, 4 semanas {g.mape_tcn_4s:.2f} %).",
        f"- **OE4-I3 (TCN mejor que el promedio móvil), a 4 semanas** (horizonte de la recomendación): "
        f"{comparar(g.mape_tcn_4s, g.mape_pm_4s)}.",
        f"- **OE4-I3 a 1 semana:** {comparar(g.mape_tcn_1s, g.mape_pm_1s)}.",
        "- **Método que usará el sistema por tostador (ADR-0003, decidido con la validación):** "
        + ", ".join(f"{t} → {m}" for t, m in metodos.items()) + ".",
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--semanas-prueba", type=int, default=6, help="Charter M4: 6 semanas por tostador")
    ap.add_argument("--semanas-validacion", type=int, default=12)
    ap.add_argument("--semillas", type=int, default=5)
    ap.add_argument("--sin-calendario", action="store_true")
    ap.add_argument("--perdida", choices=["mse", "l1"], default="l1")
    ap.add_argument("--salida", default="models/tcn_global.pt")
    ap.add_argument("--informe", default="informes")
    args = ap.parse_args()

    cfg = replace(
        Config(),
        semanas_prueba=args.semanas_prueba,
        semanas_validacion=args.semanas_validacion,
        semillas=args.semillas,
        calendario=not args.sin_calendario,
        perdida=args.perdida,
    )
    series = cargar_series(args.csv)
    cortas = [s.id for s in series if len(s.kg) < cfg.minimo_semanas]
    if cortas:
        print(f"Historial insuficiente (< {cfg.minimo_semanas} semanas): {cortas} usarán el promedio móvil.")
    if len(cortas) == len(series):
        raise SystemExit("Ningún tostador tiene historial suficiente: se usa el promedio móvil para todos.")

    modelos = entrenar_conjunto(series, cfg)
    metodos = elegir_metodo_por_tostador(series, modelos, cfg)
    val = resumen_mape(errores([s for s in series if s.id not in cortas], modelos, cfg, "validacion"))
    prueba = resumen_mape(errores([s for s in series if s.id not in cortas], modelos, cfg, "prueba"))

    sem = sorted({len(s.kg) for s in series})
    texto = f"""# HU-19: evaluación de la TCN frente al promedio móvil de 4 semanas

## Protocolo

- Datos: `{Path(args.csv).name}`, {len(series)} tostadores, {sem[0]}–{sem[-1]} semanas cada uno (datos sintéticos, plan de contingencia H06a).
- Partición temporal por tostador: entrenamiento = todo menos las últimas {cfg.semanas_validacion + cfg.semanas_prueba} semanas;
  validación = {cfg.semanas_validacion} semanas; **prueba = últimas {cfg.semanas_prueba} semanas**, apartadas antes de entrenar.
- Modelo: una TCN **global** (convoluciones causales dilatadas, canales {list(cfg.canales)}), ventana de {cfg.ventana} semanas,
  pronóstico directo de {cfg.horizonte} semanas, series normalizadas por tostador con estadísticas del tramo de entrenamiento,
  mes del año (seno/coseno) como entrada{'' if cfg.calendario else ' (DESACTIVADO)'}, pérdida {cfg.perdida.upper()},
  conjunto de {cfg.semillas} redes con distinta inicialización y parada temprana por pérdida de validación.
- Evaluación con **origen rodante**: en cada semana de la región evaluada se pronostica con la historia observada hasta ese momento.
  "1 semana" es el primer paso; "4 semanas" reúne los 4 pasos de cada origen cuyo horizonte completo cae dentro de la región.
- Referencia: promedio móvil de 4 semanas sobre exactamente las mismas semanas.
- Elección de la configuración (calendario, pérdida): solo con el MAPE de validación, nunca con el de prueba.

## Resultados en el conjunto de prueba ({cfg.semanas_prueba} semanas por tostador)

{tabla_md(prueba)}

## Resultados en validación (usados para elegir el método por tostador)

{tabla_md(val)}

## Veredicto

{chr(10).join(veredicto(prueba, metodos))}

## Limitaciones

- Los datos son simulados con supuestos documentados; el desempeño con historiales reales puede ser distinto.
- La prueba es corta ({cfg.semanas_prueba} semanas por tostador): a 4 semanas hay pocos orígenes completos por tostador, así que las
  diferencias pequeñas entre métodos no son concluyentes. Conviene repetir con `--semanas-prueba 12` como análisis de sensibilidad.
- La elección de método por tostador es inestable en los casos límite (p. ej. T02 pasa de promedio móvil a TCN al cambiar el tamaño de la prueba): conviene reevaluarla cuando haya datos reales.
- La validación se usó para elegir la configuración y el método por tostador; por eso su MAPE es algo optimista y no se informa como resultado final.
"""
    Path(args.informe).mkdir(parents=True, exist_ok=True)
    sufijo = "" if args.semanas_prueba == 6 else f"-prueba{args.semanas_prueba}"
    (Path(args.informe) / f"hu19-informe{sufijo}.md").write_text(texto, encoding="utf-8")
    (Path(args.informe) / f"hu19-resultados{sufijo}.json").write_text(
        json.dumps(
            {"config": config_a_dict(cfg), "metodos": metodos, "prueba": prueba.round(3).to_dict("index"),
             "validacion": val.round(3).to_dict("index")},
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"config": config_a_dict(cfg), "estados": [m.state_dict() for m in modelos], "metodos": metodos}, args.salida)

    print(texto)
    print(f"Modelo guardado en {args.salida}; informe en {args.informe}/")


if __name__ == "__main__":
    main()
