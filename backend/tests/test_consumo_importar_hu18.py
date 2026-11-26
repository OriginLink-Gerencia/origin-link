"""HU-18 Importar el historial de consumo desde CSV o Excel."""

import datetime as dt
import io

import pytest
from openpyxl import Workbook
from sqlalchemy import select

from app.models.abastecimiento import ConsumoHistorico

URL = "/api/v1/consumo-historico/importar"


def csv(*filas: str, cabecera: str = "fecha,kg_consumidos") -> bytes:
    return "\n".join([cabecera, *filas]).encode()


def subir(cliente, contenido: bytes, nombre: str = "consumo.csv"):
    return cliente.post(URL, files={"archivo": (nombre, contenido)})


def semanas(db, tostador_id):
    filas = db.scalars(
        select(ConsumoHistorico).where(ConsumoHistorico.tostador_id == tostador_id).order_by(ConsumoHistorico.semana)
    )
    return [(f.semana, float(f.kg_consumidos)) for f in filas]


def test_escenario1_importa_un_csv_semanal(como, db, usuarios):
    r = subir(como("a"), csv("2026-11-02,7", "2026-11-09,8.5", "2026-11-16,9"))
    assert r.status_code == 200
    assert r.json() == {"semanas_importadas": 3, "desde": "2026-11-02", "hasta": "2026-11-16", "errores": []}
    assert semanas(db, usuarios["a"].organizacion_id) == [
        (dt.date(2026, 11, 2), 7.0),
        (dt.date(2026, 11, 9), 8.5),
        (dt.date(2026, 11, 16), 9.0),
    ]


def test_los_datos_diarios_se_suman_por_semana_con_lunes_como_inicio(como, db, usuarios):
    # 4/11 (miércoles) y 8/11 (domingo) caen en la semana del 2/11; el lunes 9/11 abre la siguiente
    r = subir(como("a"), csv("2026-11-04,3", "2026-11-08,2", "2026-11-09,4"))
    assert r.json()["semanas_importadas"] == 2
    assert semanas(db, usuarios["a"].organizacion_id) == [(dt.date(2026, 11, 2), 5.0), (dt.date(2026, 11, 9), 4.0)]


def test_importa_un_archivo_excel(como, db, usuarios):
    libro = Workbook()
    hoja = libro.active
    hoja.append(["fecha", "kg_consumidos"])
    hoja.append([dt.date(2026, 11, 2), 7])
    hoja.append([dt.date(2026, 11, 9), 8])
    memoria = io.BytesIO()
    libro.save(memoria)
    r = subir(como("a"), memoria.getvalue(), "consumo.xlsx")
    assert r.status_code == 200 and r.json()["semanas_importadas"] == 2
    assert semanas(db, usuarios["a"].organizacion_id)[0] == (dt.date(2026, 11, 2), 7.0)


def test_acepta_encabezados_con_mayusculas_y_coma_decimal(como, db, usuarios):
    r = subir(como("a"), b'Fecha;KG_Consumidos\n2026-11-02;"7,5"')
    assert r.status_code == 200 and r.json()["semanas_importadas"] == 1
    assert semanas(db, usuarios["a"].organizacion_id) == [(dt.date(2026, 11, 2), 7.5)]


def test_escenario2_con_errores_no_se_importa_nada_y_se_indica_la_fila(como, db, usuarios):
    r = subir(como("a"), csv("2026-11-02,7", "2026-11-09,-3", "no-es-fecha,4", "2026-11-23,abc", "2026-11-30,"))
    cuerpo = r.json()
    assert r.status_code == 200 and cuerpo["semanas_importadas"] == 0
    assert [(e["fila"], e["error"]) for e in cuerpo["errores"]] == [
        (3, "kg_consumidos negativo"),
        (4, "fecha no válida"),
        (5, "kg_consumidos no es un número"),
        (6, "kg_consumidos vacío"),
    ]
    assert semanas(db, usuarios["a"].organizacion_id) == []


def test_faltan_columnas(como):
    r = subir(como("a"), b"dia,kilos\n2026-11-02,7")
    assert r.status_code == 400
    assert "fecha" in r.json()["detail"] and "kg_consumidos" in r.json()["detail"]


@pytest.mark.parametrize("nombre", ["consumo.pdf", "consumo", "consumo.csv.exe"])
def test_solo_csv_o_xlsx(como, nombre):
    assert subir(como("a"), csv("2026-11-02,7"), nombre).status_code == 400


def test_archivo_vacio_o_sin_filas(como):
    assert subir(como("a"), b"").status_code == 400
    assert subir(como("a"), csv()).status_code == 400


def test_reimportar_reemplaza_las_semanas_del_archivo_y_conserva_las_demas(como, db, usuarios):
    c = como("a")
    subir(c, csv("2026-11-02,7", "2026-11-09,8"))
    r = subir(c, csv("2026-11-09,20", "2026-11-16,9"))
    assert r.json()["semanas_importadas"] == 2
    assert semanas(db, usuarios["a"].organizacion_id) == [
        (dt.date(2026, 11, 2), 7.0),
        (dt.date(2026, 11, 9), 20.0),
        (dt.date(2026, 11, 16), 9.0),
    ]


def test_cada_tostador_importa_solo_a_su_empresa(como, db, usuarios):
    subir(como("a"), csv("2026-11-02,7"))
    subir(como("b"), csv("2026-11-02,99"))
    assert semanas(db, usuarios["a"].organizacion_id) == [(dt.date(2026, 11, 2), 7.0)]
    assert semanas(db, usuarios["b"].organizacion_id) == [(dt.date(2026, 11, 2), 99.0)]


def test_la_cooperativa_no_puede_importar(como):
    assert subir(como("coop"), csv("2026-11-02,7")).status_code == 403


def test_rechaza_archivos_demasiado_grandes(como):
    filas = [f"2026-11-02,{i}" for i in range(60_000)]
    assert subir(como("a"), csv(*filas)).status_code == 413
