"""Generador de datos sintéticos de Origin Link (plan de contingencia del hito H06a).

Los tostadores entrevistados no entregaron su historial de consumo, así que se simula a partir de los
supuestos documentados en ml/datos_sinteticos/README.md (entrevista 1 y documentos del entrevistado 2).

Qué hace:
1. Lee los datos maestros generados en Mockaroo (proveedores.csv y lotes.csv) y los valida.
2. Crea 4 tostadores ficticios y les asigna proveedores (directorio de cada tostador).
3. Simula semana a semana el consumo de café verde de cada tostador: tendencia + estacionalidad +
   autocorrelación + eventos + ruido.
4. Simula su política de compras (repone cuando el stock no cubre el plazo de entrega + cobertura),
   las recepciones (con diferencias calibradas con el seguimiento de compras del entrevistado 2) y
   los movimientos de inventario. Así compras, recepciones, existencias y consumo son coherentes.
5. Separa el horizonte en dos partes, como pasaría con un tostador real:
   - Historial (todas las semanas antes de empezar a usar la app) → consumo_historico.csv (HU-18).
   - Uso de la app (últimas N semanas) → compras, recepciones y movimientos registrados en la app.

Uso:
    cd ml
    python generar_datos.py                       # usa datos_sinteticos/mockaroo/*.csv
    python generar_datos.py --maestros-demo       # sin Mockaroo: genera maestros de ejemplo
    python generar_datos.py --semilla 7 --semanas 104 --semanas-app 8

Salida en ml/datos_sinteticos/generados/ (ver README de esa carpeta).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent / "datos_sinteticos"
PROCESOS = {"LAVADO", "NATURAL", "HONEY", "ANAEROBICO", "OTRO"}

# --------------------------------------------------------------------------- supuestos

# Estacionalidad mensual del consumo en Lima (supuesto a validar con los tostadores):
# más consumo en invierno (jun-sep), Fiestas Patrias, Día del Café Peruano (agosto) y diciembre;
# menos en verano (ene-mar).
ESTACIONALIDAD = {1: 0.94, 2: 0.90, 3: 0.95, 4: 0.99, 5: 1.01, 6: 1.06, 7: 1.10, 8: 1.09, 9: 1.04, 10: 0.99,
                  11: 1.01, 12: 1.12}  # fmt: skip


@dataclass
class PerfilTostador:
    id: str
    nombre: str
    distrito: str
    kg_semana_base: float  # consumo semanal al inicio del horizonte
    tendencia_semanal: float  # crecimiento por semana (0.002 = +0.2 %)
    ruido: float  # desviación del ruido en escala logarítmica
    eventos_por_anio: float  # pedidos corporativos o ferias (+20 % a +40 % una semana)


PERFILES = [
    # Perfil de la entrevista 1: compras cada 2-3 semanas, 25-30 kg al mes (≈ 6-7 kg/semana).
    PerfilTostador("T01", "Tostaduría Del Valle (demo)", "Miraflores", 6.5, 0.0010, 0.07, 2),
    PerfilTostador("T02", "Café Puerto Barranco (demo)", "Barranco", 3.8, 0.0055, 0.09, 1),
    PerfilTostador("T03", "Tostadora Andina (demo)", "San Isidro", 12.0, 0.0005, 0.06, 3),
    PerfilTostador("T04", "Microtostaduría Surco (demo)", "Santiago de Surco", 2.4, 0.0020, 0.12, 1),
]

SEMANAS_COBERTURA = 2  # default de organizaciones.semanas_cobertura (HU-21)


# --------------------------------------------------------------------------- utilidades


def lunes(d: date) -> date:
    return d - timedelta(days=d.weekday())


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sin_tildes.strip().upper()


def redondear(x: float, decimales: int = 2) -> float:
    return float(round(x, decimales))


# --------------------------------------------------------------------------- maestros


def maestros_demo(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Maestros de ejemplo con el mismo formato que los de Mockaroo (para probar sin Mockaroo)."""
    nombres = ["Coop. Agraria Cafetalera Valle Alto", "Asociación de Productores Flor de Café",
               "Coop. Agraria Selva Central", "Cafetaleros Unidos de Jaén", "Asociación Café Sandia",
               "Coop. Agraria Pichanaki", "Productores Orgánicos Villa Rica", "Coop. Café Rodríguez de Mendoza"]  # fmt: skip
    regiones = ["Cajamarca - Jaén", "Amazonas - Rodríguez de Mendoza", "Junín - Chanchamayo", "Cusco - La Convención",
                "Puno - Sandia", "San Martín - Moyobamba", "Pasco - Villa Rica", "Junín - Pichanaki"]  # fmt: skip
    prov = pd.DataFrame({
        "proveedor_id": range(1, 9),
        "nombre": nombres,
        "region": regiones,
        "ruc": [f"20{rng.integers(100_000_000, 999_999_999)}" for _ in range(8)],
        "contacto_nombre": ["Ana Quispe", "Luis Huamán", "Rosa Flores", "Jorge Torres", "Carmen Mamani",
                            "Pedro Rojas", "Elena Vargas", "Víctor Chávez"],  # fmt: skip
        "contacto_telefono": [f"9{rng.integers(10_000_000, 99_999_999)}" for _ in range(8)],
        "contacto_email": [f"ventas{i}@cooperativa-demo.pe" for i in range(1, 9)],
        "certificacion": rng.choice(["Orgánica", "Fair Trade", "Orgánica y Fair Trade", "Ninguna"], 8),
        "tiene_cuenta": [True, True, True, True, True, False, False, False],
    })  # fmt: skip
    filas = []
    for lote_id in range(1, 31):
        p = prov.iloc[(lote_id - 1) % 8]
        filas.append({
            "lote_id": lote_id,
            "proveedor_id": int(p.proveedor_id),
            "codigo": f"LOT-{2026 if lote_id % 3 else 2025}-{lote_id:03d}",
            "region": p.region,
            "finca": rng.choice(["El Mirador", "La Esperanza", "San José", "Las Orquídeas", "Santa Rosa"]),
            "variedad": rng.choice(["Caturra", "Typica", "Bourbon", "Catuaí", "Pache", "Geisha", "Catimor"]),
            "proceso": rng.choice(["LAVADO", "NATURAL", "HONEY", "ANAEROBICO"], p=[0.6, 0.2, 0.15, 0.05]),
            "cosecha": "2026" if lote_id % 3 else "2025",
            "altitud_msnm": int(rng.integers(1200, 2100)),
            "caracteristicas": rng.choice(["Chocolate y panela", "Frutos rojos, acidez brillante",
                                           "Cítricos y miel", "Caramelo y nueces"]),  # fmt: skip
            "cantidad_disponible_kg": float(rng.integers(60, 600)),
            "precio_kg": redondear(rng.uniform(26, 42)),
            "cantidad_minima_kg": float(rng.choice([5, 10, 15, 30], p=[0.3, 0.35, 0.25, 0.1])),
            "plazo_entrega_dias": int(rng.choice([2, 4, 7, 10, 15], p=[0.1, 0.2, 0.4, 0.2, 0.1])),
        })  # fmt: skip
    return prov, pd.DataFrame(filas)


def cargar_maestros(directorio: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Lee y valida los CSV de Mockaroo. Devuelve también la lista de advertencias."""
    avisos: list[str] = []
    prov = pd.read_csv(directorio / "proveedores.csv")
    lotes = pd.read_csv(directorio / "lotes.csv")

    req_p = {"proveedor_id", "nombre", "region", "tiene_cuenta"}
    req_l = {"lote_id", "proveedor_id", "codigo", "variedad", "proceso", "cosecha", "altitud_msnm",
             "cantidad_disponible_kg", "precio_kg", "cantidad_minima_kg", "plazo_entrega_dias"}  # fmt: skip
    for nombre, df, req in [("proveedores.csv", prov, req_p), ("lotes.csv", lotes, req_l)]:
        faltan = req - set(df.columns)
        if faltan:
            raise SystemExit(f"{nombre}: faltan columnas {sorted(faltan)}. Revisa el esquema de Mockaroo.")

    prov["tiene_cuenta"] = prov["tiene_cuenta"].astype(str).str.lower().isin(["true", "1", "si", "sí", "yes"])
    if prov["tiene_cuenta"].sum() < 2:
        raise SystemExit("proveedores.csv: se necesitan al menos 2 proveedores con tiene_cuenta = true.")

    lotes["proceso"] = lotes["proceso"].map(normalizar).replace({"ANAEROBIO": "ANAEROBICO"})
    malos = ~lotes["proceso"].isin(PROCESOS)
    if malos.any():
        avisos.append(f"{int(malos.sum())} lotes con proceso desconocido → OTRO")
        lotes.loc[malos, "proceso"] = "OTRO"

    huerfanos = ~lotes["proveedor_id"].isin(prov["proveedor_id"])
    if huerfanos.any():
        raise SystemExit(f"lotes.csv: {int(huerfanos.sum())} lotes con proveedor_id que no existe en proveedores.csv")

    for col, minimo in [("cantidad_disponible_kg", 0), ("precio_kg", 0.01), ("cantidad_minima_kg", 0),
                        ("plazo_entrega_dias", 0), ("altitud_msnm", 0)]:  # fmt: skip
        lotes[col] = pd.to_numeric(lotes[col], errors="coerce")
        if lotes[col].isna().any() or (lotes[col] < minimo).any():
            raise SystemExit(f"lotes.csv: la columna {col} tiene valores vacíos o menores que {minimo}")
    lotes["cosecha"] = lotes["cosecha"].astype(str)
    # La procedencia del lote es la región de su proveedor (Mockaroo no puede cruzar dos esquemas)
    lotes["region"] = lotes["proveedor_id"].map(prov.set_index("proveedor_id")["region"])
    if lotes["lote_id"].duplicated().any() or lotes["codigo"].duplicated().any():
        raise SystemExit("lotes.csv: hay lote_id o codigo repetidos")
    sin_lotes = set(prov["proveedor_id"]) - set(lotes["proveedor_id"])
    if sin_lotes:
        avisos.append(f"Proveedores sin lotes (no se usarán para compras): {sorted(sin_lotes)}")
    return prov, lotes, avisos


# --------------------------------------------------------------------------- simulación


def serie_consumo(perfil: PerfilTostador, semanas: list[date], rng: np.random.Generator) -> np.ndarray:
    """Consumo semanal (kg): base × tendencia × estacionalidad × eventos × ruido AR(1)."""
    n = len(semanas)
    ar = np.zeros(n)
    for t in range(1, n):  # autocorrelación: una semana alta tiende a seguir de otra alta
        ar[t] = 0.5 * ar[t - 1] + rng.normal(0, perfil.ruido)
    eventos = np.ones(n)
    for t in np.flatnonzero(rng.random(n) < perfil.eventos_por_anio / 52):
        eventos[t] = rng.uniform(1.2, 1.4)
    t = np.arange(n)
    est = np.array([ESTACIONALIDAD[s.month] for s in semanas])
    kg = perfil.kg_semana_base * (1 + perfil.tendencia_semanal) ** t * est * eventos * np.exp(ar)
    return np.round(np.clip(kg, 0.1, None), 2)


def diferencia_recepcion(rng: np.random.Generator) -> tuple[float, str | None]:
    """Fracción recibida vs. acordada, calibrada con el seguimiento de compras 2021 del entrevistado 2
    (mediana −7.8 % en lotes de toneladas, con entregas parciales). Para lotes pequeños de un tostador se
    asume la mayoría sin diferencia o con mermas leves por humedad."""
    r = rng.random()
    if r < 0.45:
        return 0.0, None
    if r < 0.80:
        return -rng.uniform(0.005, 0.03), "Merma leve: sacos con humedad alta"
    if r < 0.92:
        return rng.uniform(0.005, 0.02), "Peso neto mayor al acordado"
    return -rng.uniform(0.08, 0.15), "Entrega parcial: faltan sacos, el proveedor completará después"


def simular(prov: pd.DataFrame, lotes: pd.DataFrame, semanas_total: int, semanas_app: int, fin: date, semilla: int):
    rng = np.random.default_rng(semilla)
    semanas = [lunes(fin) - timedelta(weeks=semanas_total - 1 - i) for i in range(semanas_total)]
    inicio_app = semanas[-semanas_app]

    con_cuenta = prov[prov.tiene_cuenta & prov.proveedor_id.isin(lotes.proveedor_id)].proveedor_id.tolist()
    sin_cuenta = prov[~prov.tiene_cuenta & prov.proveedor_id.isin(lotes.proveedor_id)].proveedor_id.tolist()
    rng.shuffle(sin_cuenta)

    tostadores, directorio, consumo_hist, consumo_full = [], [], [], []
    compras, recepciones, movimientos = [], [], []
    stats = {}
    dir_id = compra_id = rec_id = mov_id = 0

    for i, perfil in enumerate(PERFILES):
        tostadores.append({
            "tostador_id": perfil.id, "nombre": perfil.nombre, "ruc": f"20{rng.integers(100_000_000, 999_999_999)}",
            "region": f"Lima - {perfil.distrito}", "usuario_nombre": f"Usuario {perfil.id}",
            "email": f"{perfil.id.lower()}@demo.originlink.pe", "password_demo": "OriginLink2026!",
            "semanas_cobertura": SEMANAS_COBERTURA, "kg_semana_base": perfil.kg_semana_base,
        })  # fmt: skip
        # Directorio: 2 cooperativas con cuenta (vinculadas) + 1 sin cuenta si hay disponible.
        elegidos = list(rng.choice(con_cuenta, size=min(2, len(con_cuenta)), replace=False))
        propios = [sin_cuenta[i]] if i < len(sin_cuenta) else []
        mapa_dir = {}
        for pid in elegidos + propios:
            dir_id += 1
            p = prov[prov.proveedor_id == pid].iloc[0]
            mapa_dir[int(pid)] = dir_id
            directorio.append({
                "directorio_id": dir_id, "tostador_id": perfil.id, "proveedor_id": int(pid), "nombre": p.nombre,
                "region": p.region, "contacto_nombre": p.get("contacto_nombre"),
                "contacto_telefono": p.get("contacto_telefono"), "contacto_email": p.get("contacto_email"),
                "estado_vinculo": "VINCULADO" if pid in elegidos else "SIN_VINCULAR",
            })  # fmt: skip
        mis_lotes = lotes[lotes.proveedor_id.isin(mapa_dir.keys())].reset_index(drop=True)

        # Serie con su propia semilla: no cambia aunque cambien los maestros de Mockaroo
        kg = serie_consumo(perfil, semanas, np.random.default_rng([semilla, i]))
        stock: dict[int, float] = {}  # lote_id -> kg
        primer = mis_lotes.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        stock[int(primer.lote_id)] = round(3 * perfil.kg_semana_base, 2)  # stock inicial: 3 semanas
        pendientes: list[dict] = []
        quiebres = 0

        for t, sem in enumerate(semanas):
            en_app = sem >= inicio_app
            # 1) Recepciones que llegan esta semana
            # (llega a más tardar el jueves; si llega viernes o fin de semana, se usa desde la semana siguiente)
            for c in [c for c in pendientes if c["fecha_recepcion"] <= sem + timedelta(days=3)]:
                pendientes.remove(c)
                frac, obs = diferencia_recepcion(rng)
                recibido = round(c["cantidad_kg"] * (1 + frac), 2)
                stock[c["lote_id"]] = round(stock.get(c["lote_id"], 0) + recibido, 2)
                fecha_rec = c["fecha_recepcion"]
                if c["_registrar"] and fecha_rec <= fin:
                    rec_id += 1
                    mov_id += 1
                    c["estado"] = "RECIBIDA"
                    recepciones.append({"recepcion_id": rec_id, "compra_id": c["compra_id"], "fecha_recepcion": fecha_rec,
                                        "cantidad_recibida_kg": recibido, "diferencia_kg": round(recibido - c["cantidad_kg"], 2),
                                        "observaciones": obs})  # fmt: skip
                    movimientos.append({"movimiento_id": mov_id, "tostador_id": perfil.id, "lote_id": c["lote_id"],
                                        "recepcion_id": rec_id, "tipo": "ENTRADA", "cantidad_kg": recibido,
                                        "fecha": fecha_rec, "motivo": None})  # fmt: skip

            # 2) Inventario inicial al empezar a usar la app (ajuste con motivo)
            if sem == inicio_app:
                for lote_id, q in stock.items():
                    if q > 0:
                        mov_id += 1
                        movimientos.append({"movimiento_id": mov_id, "tostador_id": perfil.id, "lote_id": lote_id,
                                            "recepcion_id": None, "tipo": "AJUSTE", "cantidad_kg": round(q, 2),
                                            "fecha": sem, "motivo": "Inventario inicial al empezar a usar Origin Link"})  # fmt: skip

            # 3) Consumo de la semana (FIFO por lote)
            restante = float(kg[t])
            for lote_id in list(stock):
                if restante <= 0:
                    break
                usado = round(min(stock[lote_id], restante), 2)
                if usado <= 0:
                    continue
                stock[lote_id] = round(stock[lote_id] - usado, 2)
                restante = round(restante - usado, 2)
                if en_app:
                    mov_id += 1
                    movimientos.append({"movimiento_id": mov_id, "tostador_id": perfil.id, "lote_id": lote_id,
                                        "recepcion_id": None, "tipo": "CONSUMO", "cantidad_kg": usado,
                                        "fecha": sem + timedelta(days=4), "motivo": None})  # fmt: skip
            if restante > 0.01:
                quiebres += 1
            consumo_full.append({"tostador_id": perfil.id, "fecha": sem, "kg_consumidos": float(kg[t])})
            if not en_app:
                consumo_hist.append({"tostador_id": perfil.id, "semana": sem, "kg_consumidos": float(kg[t])})

            # 4) Merma ocasional (≈ 1 de cada 8 semanas)
            if en_app and rng.random() < 0.125:
                lote_id = max(stock, key=stock.get)
                q = round(min(stock[lote_id], rng.uniform(0.2, 0.6)), 2)
                if q > 0:
                    stock[lote_id] = round(stock[lote_id] - q, 2)
                    mov_id += 1
                    movimientos.append({"movimiento_id": mov_id, "tostador_id": perfil.id, "lote_id": lote_id,
                                        "recepcion_id": None, "tipo": "MERMA", "cantidad_kg": q,
                                        "fecha": sem + timedelta(days=2), "motivo": "Granos defectuosos al seleccionar"})  # fmt: skip

            # 5) Política de compra: reponer si stock + pedidos pendientes no cubren el plazo + cobertura
            promedio = float(np.mean(kg[max(0, t - 3) : t + 1]))
            lote = mis_lotes.iloc[int(rng.integers(len(mis_lotes)))]
            semanas_plazo = math.ceil(lote.plazo_entrega_dias / 7)
            disponible = sum(stock.values()) + sum(c["cantidad_kg"] for c in pendientes)
            necesidad = promedio * (semanas_plazo + SEMANAS_COBERTURA)
            if disponible < promedio * (semanas_plazo + 1.5):
                cantidad = max(float(lote.cantidad_minima_kg), math.ceil(necesidad - disponible + promedio))
                fecha_compra = sem + timedelta(days=int(rng.integers(0, 3)))
                c = {"lote_id": int(lote.lote_id), "cantidad_kg": float(cantidad),
                     "fecha_entrega_acordada": fecha_compra + timedelta(days=int(lote.plazo_entrega_dias)),
                     "_registrar": fecha_compra >= inicio_app}  # fmt: skip
                c["fecha_recepcion"] = c["fecha_entrega_acordada"] + timedelta(days=int(rng.integers(0, 2)))
                if c["_registrar"]:
                    compra_id += 1
                    c.update({"compra_id": compra_id, "estado": "PENDIENTE"})
                    compras.append({"compra_id": compra_id, "tostador_id": perfil.id,
                                    "directorio_id": mapa_dir[int(lote.proveedor_id)], "lote_id": int(lote.lote_id),
                                    "cantidad_kg": float(cantidad), "precio_kg": float(lote.precio_kg),
                                    "fecha_compra": fecha_compra, "fecha_entrega_acordada": c["fecha_entrega_acordada"],
                                    "estado": "PENDIENTE", "observaciones": None, "_ref": c})  # fmt: skip
                pendientes.append(c)

        stats[perfil.id] = {
            "semanas": len(semanas), "kg_promedio_semana": redondear(float(kg.mean())),
            "kg_promedio_mes": redondear(float(kg.mean()) * 52 / 12), "semanas_con_quiebre_de_stock": quiebres,
            "existencias_finales_kg": redondear(sum(stock.values())),
        }  # fmt: skip

    for c in compras:  # estado final de cada compra
        c["estado"] = c.pop("_ref")["estado"]

    return {
        "tostadores": pd.DataFrame(tostadores),
        "directorio_proveedores": pd.DataFrame(directorio),
        "consumo_historico": pd.DataFrame(consumo_hist),
        "consumo_semanal_completo": pd.DataFrame(consumo_full),
        "compras": pd.DataFrame(compras),
        "recepciones": pd.DataFrame(recepciones),
        "movimientos": pd.DataFrame(movimientos),
    }, stats, inicio_app


# --------------------------------------------------------------------------- salida


def guardar(salida: Path, prov: pd.DataFrame, lotes: pd.DataFrame, tablas: dict, stats: dict, meta: dict) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    prov.to_csv(salida / "proveedores.csv", index=False)
    lotes.to_csv(salida / "lotes.csv", index=False)
    for nombre, df in tablas.items():
        df.to_csv(salida / f"{nombre}.csv", index=False)

    # Un archivo por tostador en el formato de importación de HU-18 (fecha, kg_consumidos)
    imp = salida / "importar_hu18"
    imp.mkdir(exist_ok=True)
    for tid, g in tablas["consumo_historico"].groupby("tostador_id"):
        g.rename(columns={"semana": "fecha"})[["fecha", "kg_consumidos"]].to_csv(imp / f"consumo_{tid}.csv", index=False)

    (salida / "resumen.json").write_text(
        json.dumps({**meta, "por_tostador": stats}, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    try:  # gráfico para el informe y para las sesiones de validación (opcional)
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        full = tablas["consumo_semanal_completo"]
        fig, ax = plt.subplots(figsize=(11, 5))
        for tid, g in full.groupby("tostador_id"):
            nombre = tablas["tostadores"].set_index("tostador_id").loc[tid, "nombre"]
            ax.plot(pd.to_datetime(g["fecha"]), g["kg_consumidos"], label=f"{tid} · {nombre}", linewidth=1.4)
        ax.axvline(pd.to_datetime(meta["inicio_app"]), color="gray", linestyle="--", linewidth=1)
        ax.text(pd.to_datetime(meta["inicio_app"]), ax.get_ylim()[0], " inicio de uso\n de la app", color="gray", va="bottom")
        ax.set_title("Consumo semanal de café verde (datos sintéticos)")
        ax.set_ylabel("kg por semana")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(salida / "consumo_semanal.png", dpi=150)
    except ImportError:
        pass


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mockaroo", default=str(BASE / "mockaroo"), help="Carpeta con proveedores.csv y lotes.csv")
    p.add_argument("--maestros-demo", action="store_true", help="No usar Mockaroo: generar maestros de ejemplo")
    p.add_argument("--salida", default=str(BASE / "generados"))
    p.add_argument("--semanas", type=int, default=104, help="Semanas totales de consumo (2 años)")
    p.add_argument("--semanas-app", type=int, default=8, help="Últimas semanas registradas dentro de la app")
    p.add_argument("--fin", default="2026-11-16", help="Lunes de la última semana (YYYY-MM-DD)")
    p.add_argument("--semilla", type=int, default=42, help="Misma semilla = mismos datos")
    a = p.parse_args()

    rng = np.random.default_rng(a.semilla)
    if a.maestros_demo:
        prov, lotes = maestros_demo(rng)
        avisos = ["Se usaron maestros de ejemplo (--maestros-demo), no los de Mockaroo"]
    else:
        directorio = Path(a.mockaroo)
        if not (directorio / "proveedores.csv").exists() or not (directorio / "lotes.csv").exists():
            raise SystemExit(f"No encuentro proveedores.csv y lotes.csv en {directorio}. "
                             "Descárgalos de Mockaroo (ver datos_sinteticos/README.md) o usa --maestros-demo.")  # fmt: skip
        prov, lotes, avisos = cargar_maestros(directorio)

    tablas, stats, inicio_app = simular(prov, lotes, a.semanas, a.semanas_app, date.fromisoformat(a.fin), a.semilla)
    meta = {"semilla": a.semilla, "semanas": a.semanas, "semanas_app": a.semanas_app, "fin": a.fin,
            "inicio_app": inicio_app, "origen_maestros": "demo" if a.maestros_demo else "mockaroo", "avisos": avisos,
            "filas": {k: len(v) for k, v in tablas.items()} | {"proveedores": len(prov), "lotes": len(lotes)}}  # fmt: skip
    guardar(Path(a.salida), prov, lotes, tablas, stats, meta)

    for aviso in avisos:
        print(f"Aviso: {aviso}")
    print(f"Datos generados en {a.salida}")
    for k, v in meta["filas"].items():
        print(f"  {k:<28} {v:>6} filas")
    for tid, s in stats.items():
        print(f"  {tid}: {s['kg_promedio_mes']} kg/mes en promedio · quiebres de stock: {s['semanas_con_quiebre_de_stock']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
