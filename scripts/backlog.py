"""Product Backlog del MVP de Origin Link: épicas e historias de usuario.

Fuente única del backlog. Se deriva de la matriz de trazabilidad (Project Charter 4.1), la matriz de
necesidades por actor (Anexo 5) y la EDT.

Uso:
    python scripts/backlog.py md                  # regenera docs/backlog/product-backlog.md
    python scripts/backlog.py issues --dry-run    # muestra lo que crearía en GitHub, sin crear nada
    python scripts/backlog.py issues              # crea labels, milestones (sprints), épicas e historias
    python scripts/backlog.py issues --proyecto 1 # además agrega los issues al GitHub Project número 1
    python scripts/backlog.py actualizar --dry-run  # muestra qué issues existentes cambiarían
    python scripts/backlog.py actualizar          # actualiza el cuerpo de los issues existentes,
                                                  # conservando las casillas ya marcadas

Requisitos para `issues`: GitHub CLI (https://cli.github.com) y `gh auth login`.
Para `--proyecto` también: `gh auth refresh -s project`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = "OriginLink-Gerencia/origin-link"
ORG = "OriginLink-Gerencia"

SPRINTS = {
    "Sprint A": ("2026-11-22T23:59:59Z", "Flujo colaborativo: acceso, proveedores, lotes, compras e inventario"),
    "Sprint B": ("2026-11-25T23:59:59Z", "Pronóstico, recomendaciones y alertas. Congelamiento de código el 25/11"),
    "Backlog futuro": (None, "Historias fuera del MVP (EDT 1.8.4: backlog de mejoras futuras)"),
}


@dataclass
class Historia:
    id: str
    titulo: str
    como: str
    quiero: str
    para: str
    criterios: list[tuple[str, str, str, str]]  # (escenario, dado, cuando, entonces)
    trazabilidad: str
    prioridad: str  # Must | Should | Could | Won't
    puntos: int
    sprint: str
    area: list[str]  # frontend, backend, ml
    tipo: str = "historia"  # historia | tarea-tecnica


@dataclass
class Epica:
    id: str
    titulo: str
    descripcion: str
    objetivo: str
    valor: str
    historias: list[Historia] = field(default_factory=list)


TOSTADOR = "tostador"
COOP = "empresa productora o cooperativa"

EPICAS: list[Epica] = [
    Epica(
        "EP-01",
        "Identidad y acceso",
        "Registro, inicio de sesión y control de acceso por rol para tostadores y empresas productoras o "
        "cooperativas. Una cooperativa solo puede entrar a la plataforma por invitación de un tostador.",
        "OE2 · Requisito 5.0 · EDT 1.4.2",
        "Garantiza la privacidad comercial: cada tostador ve solo su información y la de sus proveedores "
        "vinculados.",
        [
            Historia(
                "HU-01", "Registrar cuenta de tostador", TOSTADOR,
                "registrarme con el nombre de mi empresa, mi correo y una contraseña",
                "gestionar mi abastecimiento de café verde en un solo lugar",
                [
                    ("Registro exitoso", "que ingreso nombre de empresa, correo válido y contraseña de al menos 8 caracteres",
                     "envío el formulario", "se crea mi cuenta con rol tostador y entro a mi panel"),
                    ("Correo duplicado", "que ya existe una cuenta con mi correo",
                     "envío el formulario", "veo el mensaje \"Ya existe una cuenta con este correo\" y no se crea otra"),
                ],
                "Req. 5.0 · OE2 · EDT 1.4.2.1", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-02", "Iniciar y cerrar sesión", "usuario de Origin Link",
                "iniciar sesión con mi correo y contraseña y cerrarla cuando termine",
                "acceder de forma segura a mi información",
                [
                    ("Credenciales correctas", "que tengo una cuenta registrada",
                     "ingreso mi correo y contraseña correctos", "entro a la plataforma según mi rol (tostador o cooperativa)"),
                    ("Credenciales incorrectas", "que ingreso una contraseña equivocada",
                     "intento iniciar sesión", "veo \"Correo o contraseña incorrectos\" sin indicar cuál de los dos falló"),
                    ("Cerrar sesión", "que tengo la sesión iniciada",
                     "hago clic en \"Cerrar sesión\"", "vuelvo a la pantalla de inicio de sesión y no puedo acceder sin ingresar de nuevo"),
                ],
                "Req. 5.0 · OE2 · EDT 1.4.2.1", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-03", "Crear cuenta de cooperativa desde una invitación", COOP,
                "crear mi cuenta usando la invitación que me envió un tostador",
                "compartir mis lotes con ese tostador sin exponerlos públicamente",
                [
                    ("Invitación válida", "que recibí un enlace de invitación vigente",
                     "lo abro y completo mis datos", "se crea mi cuenta con rol cooperativa y quedo vinculado con el tostador que me invitó"),
                    ("Sin invitación", "que no tengo invitación",
                     "intento registrarme como cooperativa", "el sistema no me permite crear la cuenta"),
                    ("Invitación vencida o usada", "que el enlace ya fue usado o venció",
                     "lo abro", "veo \"Invitación no válida\" y la indicación de pedir una nueva al tostador"),
                ],
                "Req. 5.0 y 1.1 · OE2 · EDT 1.4.2.1, 1.4.3.2", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-04", "Restringir el acceso según el rol y el vínculo", TOSTADOR,
                "que solo mis proveedores vinculados puedan ver mi información y yo solo la de ellos",
                "mantener la privacidad comercial de mis compras",
                [
                    ("Acceso a datos propios", "que soy un tostador con sesión iniciada",
                     "consulto mis compras e inventario", "solo veo registros de mi empresa"),
                    ("Acceso no autorizado", "que una cooperativa no está vinculada conmigo",
                     "intenta consultar mis datos o lotes compartidos conmigo", "la API responde 403 y no muestra información"),
                ],
                "Req. 5.0 · OE2 · EDT 1.4.2.2", "Must", 2, "Sprint A", ["backend"],
            ),
        ],
    ),
    Epica(
        "EP-02",
        "Proveedores y relaciones privadas",
        "El tostador registra a sus proveedores de café verde y los invita a vincularse de forma privada.",
        "OE2 · Requisito 1.1 · EDT 1.4.3",
        "Reemplaza la coordinación informal por WhatsApp y hojas de cálculo (entrevista 1) por un canal "
        "privado y ordenado.",
        [
            Historia(
                "HU-05", "Registrar un proveedor", TOSTADOR,
                "registrar a mis proveedores con su nombre, región de origen y datos de contacto",
                "tener centralizada la información de quién me abastece",
                [
                    ("Registro de proveedor", "que estoy en la sección Proveedores",
                     "ingreso nombre, región y contacto y guardo", "el proveedor aparece en mi lista con estado \"Sin vincular\""),
                    ("Datos obligatorios", "que dejo vacío el nombre del proveedor",
                     "intento guardar", "veo que el nombre es obligatorio y no se guarda"),
                ],
                "Req. 1.1 · OE2 · EDT 1.4.3.1", "Must", 2, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-06", "Invitar a un proveedor a vincularse", TOSTADOR,
                "generar una invitación para un proveedor registrado",
                "que pueda publicarme sus lotes directamente en la plataforma",
                [
                    ("Generar invitación", "que tengo un proveedor \"Sin vincular\"",
                     "hago clic en \"Invitar\"", "se genera un enlace único con vigencia de 7 días que puedo copiar y enviar"),
                    ("Proveedor ya vinculado", "que el proveedor ya está vinculado",
                     "veo su ficha", "no se muestra la opción \"Invitar\""),
                ],
                "Req. 1.1 · OE2 · EDT 1.4.3.2", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-07", "Ver mis vínculos", "usuario de Origin Link",
                "ver con quiénes estoy vinculado y el estado de cada invitación",
                "saber con quién comparto información",
                [
                    ("Lista del tostador", "que invité a varios proveedores",
                     "abro Proveedores", "veo cada uno con su estado: Sin vincular, Invitado o Vinculado"),
                    ("Lista de la cooperativa", "que soy una cooperativa vinculada a dos tostadores",
                     "abro mi panel", "veo los dos tostadores con los que comparto lotes"),
                ],
                "Req. 1.1 · OE2 · EDT 1.4.3.2", "Must", 2, "Sprint A", ["backend", "frontend"],
            ),
        ],
    ),
    Epica(
        "EP-03",
        "Gestión colaborativa de lotes",
        "La cooperativa publica sus lotes de café verde, su disponibilidad y condiciones de abastecimiento "
        "para los tostadores vinculados.",
        "OE2 · Requisitos 1.2 y 1.2.1 · EDT 1.4.4",
        "El tostador consulta información técnica y disponibilidad actualizada sin pedirla por chat "
        "(entrevistas 1, 4 y 5).",
        [
            Historia(
                "HU-08", "Publicar un lote de café verde", COOP,
                "publicar un lote con su procedencia, variedad, proceso, cosecha, altitud, cantidad y precio",
                "que mis tostadores vinculados conozcan lo que tengo disponible",
                [
                    ("Publicación exitosa", "que estoy vinculado con al menos un tostador",
                     "registro un lote con todos sus atributos y lo publico", "el lote queda visible solo para mis tostadores vinculados"),
                    ("Validación de datos", "que ingreso una altitud o cantidad negativa",
                     "intento publicar", "veo el error en el campo y el lote no se publica"),
                ],
                "Req. 1.2 · OE2 · EDT 1.4.4.1, 1.4.4.2", "Must", 5, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-09", "Consultar los lotes de mis proveedores", TOSTADOR,
                "ver los lotes publicados por mis proveedores vinculados con sus características",
                "decidir qué comprar con información completa",
                [
                    ("Lista de lotes", "que mis proveedores publicaron lotes",
                     "abro la sección Lotes", "veo cada lote con proveedor, origen, altitud, proceso, cantidad disponible y precio"),
                    ("Filtro", "que hay lotes de varios proveedores",
                     "filtro por proveedor o proceso", "solo veo los lotes que cumplen el filtro"),
                ],
                "Req. 1.2 · OE2 · EDT 1.4.4.5", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-10", "Actualizar disponibilidad y condiciones de abastecimiento", COOP,
                "actualizar la cantidad disponible, cantidad mínima de compra, precio y plazo de entrega de mis lotes",
                "que mis tostadores planifiquen con datos vigentes",
                [
                    ("Actualización", "que tengo un lote publicado",
                     "cambio su cantidad disponible o su plazo de entrega", "el tostador ve el dato nuevo y la fecha de la última actualización"),
                    ("Lote agotado", "que la cantidad disponible llega a 0",
                     "guardo el cambio", "el lote se muestra como \"Agotado\""),
                ],
                "Req. 1.2 · OE2 · EDT 1.4.4.4", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-11", "Registrar un lote de un proveedor sin cuenta", TOSTADOR,
                "registrar yo mismo un lote de un proveedor que aún no usa la plataforma",
                "llevar el control de todo mi café verde aunque no todos mis proveedores estén vinculados",
                [
                    ("Lote manual", "que tengo un proveedor \"Sin vincular\"",
                     "registro un lote a su nombre", "el lote aparece en mi lista marcado como \"Registrado por el tostador\""),
                ],
                "Req. 1.2 · OE2 · EDT 1.4.4.1", "Should", 2, "Sprint B", ["backend", "frontend"],
            ),
            Historia(
                "HU-12", "Adjuntar muestras, fichas técnicas y documentos a un lote", COOP,
                "adjuntar la ficha técnica y los resultados de evaluación de un lote",
                "que el tostador valide la calidad declarada",
                [
                    ("Adjuntar documento", "que tengo un lote publicado",
                     "adjunto un PDF de ficha técnica", "el tostador vinculado puede descargarlo desde el detalle del lote"),
                ],
                "Req. 1.2.1 · OE2 · EDT 1.4.4.3", "Could", 3, "Backlog futuro", ["backend", "frontend"],
            ),
        ],
    ),
    Epica(
        "EP-04",
        "Compras y recepciones",
        "El tostador registra sus compras y la recepción de cada lote, incluidas las diferencias entre lo "
        "acordado y lo recibido.",
        "OE2 · Requisito 2.1 · EDT 1.4.5",
        "Atiende las mermas y los incumplimientos logísticos reportados en las entrevistas 1 y 2.",
        [
            Historia(
                "HU-13", "Registrar una compra", TOSTADOR,
                "registrar una compra con el lote, la cantidad, el precio y la fecha de entrega acordada",
                "llevar el historial de mis compras por proveedor",
                [
                    ("Compra de un lote publicado", "que un lote tiene 200 kg disponibles",
                     "registro una compra de 60 kg", "la compra queda \"Pendiente de recepción\" con la fecha de entrega acordada"),
                    ("Cantidad mayor a la disponible", "que un lote tiene 50 kg disponibles",
                     "intento registrar 80 kg", "veo una advertencia de que supera lo disponible"),
                ],
                "Req. 2.1 · OE2 · EDT 1.4.5.1", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-14", "Registrar la recepción de una compra", TOSTADOR,
                "registrar los kilos efectivamente recibidos y las observaciones",
                "detectar diferencias con lo acordado y actualizar mi inventario",
                [
                    ("Recepción completa", "que tengo una compra pendiente de 60 kg",
                     "registro la recepción de 60 kg", "la compra pasa a \"Recibida\" y se crea una entrada de inventario de 60 kg"),
                    ("Recepción con diferencia", "que tengo una compra pendiente de 60 kg",
                     "registro 55 kg recibidos", "se registra una diferencia de -5 kg visible en la compra y la entrada de inventario es de 55 kg"),
                ],
                "Req. 2.1 · OE2 · EDT 1.4.5.2", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-15", "Consultar el historial de compras por proveedor", TOSTADOR,
                "ver el historial de compras y recepciones de cada proveedor",
                "negociar con información y no de memoria",
                [
                    ("Historial", "que hice varias compras a un proveedor",
                     "abro su ficha", "veo sus compras con fechas, kilos acordados, kilos recibidos y diferencias"),
                ],
                "Req. 2.1 · OE2 · EDT 1.4.5.3", "Should", 2, "Sprint B", ["backend", "frontend"],
            ),
        ],
    ),
    Epica(
        "EP-05",
        "Inventario y existencias",
        "Registro de movimientos de café verde y cálculo de existencias a partir de ellos.",
        "OE2 · Requisito 2.1.1 · EDT 1.4.6",
        "El tostador conoce su stock real y evita quiebres; además genera el historial de consumo que "
        "alimenta al modelo TCN.",
        [
            Historia(
                "HU-16", "Registrar consumos, mermas y ajustes", TOSTADOR,
                "registrar los kilos de café verde que consumo en el tostado, las mermas y los ajustes de inventario",
                "mantener mis existencias al día",
                [
                    ("Consumo", "que tengo 40 kg de un lote",
                     "registro un consumo de 8 kg", "las existencias de ese lote quedan en 32 kg"),
                    ("Consumo mayor a las existencias", "que tengo 5 kg de un lote",
                     "intento registrar un consumo de 8 kg", "veo un error y el movimiento no se registra"),
                    ("Ajuste con motivo", "que hago un conteo físico",
                     "registro un ajuste", "el sistema me exige indicar el motivo"),
                ],
                "Req. 2.1.1 · OE2 · EDT 1.4.6.1", "Must", 3, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-17", "Ver mis existencias actuales", TOSTADOR,
                "ver cuántos kilos tengo de cada lote y en total",
                "saber con qué cuento antes de planificar compras",
                [
                    ("Existencias calculadas", "que registré entradas, consumos, mermas y ajustes",
                     "abro Inventario", "veo las existencias por lote calculadas como entradas - consumos - mermas ± ajustes"),
                    ("Total y lotes agotados", "que tengo café de varios lotes y uno ya se consumió por completo",
                     "abro Inventario", "veo el total en kg como la suma de todos mis lotes y el lote consumido no aparece en la lista"),
                ],
                "Req. 2.1.1 · OE2 · EDT 1.4.6.2", "Must", 2, "Sprint A", ["backend", "frontend"],
            ),
            Historia(
                "HU-18", "Importar mi historial de consumo", TOSTADOR,
                "cargar mi historial de consumo desde un archivo CSV o Excel",
                "no duplicar el trabajo que ya hice en mis hojas de cálculo y obtener pronósticos desde el primer día",
                [
                    ("Importación válida", "que tengo un archivo con columnas fecha y kg_consumidos",
                     "lo cargo", "veo cuántas semanas se importaron y el historial queda disponible para el pronóstico"),
                    ("Archivo con errores", "que el archivo tiene fechas inválidas o kilos negativos",
                     "lo cargo", "veo las filas con error y no se importa ninguna hasta corregirlas"),
                ],
                "Req. 2.1.1 y 3.1 · OE2, OE3 · EDT 1.4.6.1, 1.5.1.1 · Anexo 5 (entrevista 4)", "Must", 3, "Sprint A",
                ["backend", "frontend"],
            ),
        ],
    ),
    Epica(
        "EP-06",
        "Pronóstico de demanda con TCN",
        "Entrenamiento, evaluación y servicio del modelo TCN que pronostica el consumo semanal del tostador, "
        "con el promedio móvil de 4 semanas como referencia y respaldo.",
        "OE3 · Requisitos 3.0 y 3.1 · EDT 1.5.1 a 1.5.3",
        "Reemplaza el cálculo empírico de reabastecimiento (entrevista 1) por un pronóstico basado en datos.",
        [
            Historia(
                "HU-19", "Entrenar y evaluar el modelo TCN", "Product Owner",
                "un informe que compare el error del modelo TCN con el del promedio móvil de 4 semanas",
                "verificar los indicadores OE3-I1 (MAPE ≤ 25 %) y OE4-I3 antes de usar el modelo",
                [
                    ("Evaluación", "que el historial de consumo está preparado y el conjunto de prueba se fijó antes de entrenar",
                     "se entrena la TCN y se evalúa en el conjunto de prueba", "se obtiene el MAPE de la TCN y del promedio móvil sobre las mismas semanas"),
                    ("Historial insuficiente", "que un tostador tiene menos semanas que el mínimo requerido",
                     "se intenta entrenar", "se documenta que para ese tostador se usará el promedio móvil"),
                ],
                "Req. 3.1 · OE3 · EDT 1.5.1.2, 1.5.2.1, 1.5.2.3", "Must", 5, "Sprint A", ["ml"],
            ),
            Historia(
                "TT-01", "Cargar los datos sintéticos de demostración (seed)", "equipo del proyecto",
                "cargar en la base de datos los tostadores, proveedores, lotes, historial, compras, recepciones y "
                "movimientos generados por ml/generar_datos.py",
                "demostrar el flujo completo y el pronóstico con datos coherentes en la revisión del 23–27 de "
                "noviembre y en las sesiones de validación (plan de contingencia del hito H06a)",
                [
                    ("Carga completa", "que la base tiene la migración aplicada y existen los CSV en ml/datos_sinteticos/generados",
                     "ejecuto python -m app.seed", "se crean los 4 tostadores con su usuario demo, las cooperativas con cuenta, "
                     "los directorios, lotes, historial, compras, recepciones y movimientos"),
                    ("Idempotencia", "que el seed ya se ejecutó",
                     "lo ejecuto otra vez", "no se duplica ningún registro"),
                    ("Coherencia", "que los datos están cargados",
                     "consulto GET /existencias con el usuario demo de T01", "el total coincide con existencias_finales_kg de resumen.json"),
                ],
                "Plan de contingencia H06a · OE3 · EDT 1.5.1.2", "Must", 3, "Sprint A", ["backend", "ml"],
                tipo="tarea-tecnica",
            ),
            Historia(
                "HU-20", "Ver el pronóstico de consumo de las próximas semanas", TOSTADOR,
                "ver cuántos kilos de café verde consumiré en las próximas 4 semanas",
                "anticipar mis compras",
                [
                    ("Pronóstico con TCN", "que tengo historial suficiente",
                     "abro Pronóstico", "veo el consumo estimado por semana para las próximas 4 semanas junto con mi consumo histórico en un gráfico"),
                    ("Respaldo", "que mi historial es insuficiente o el modelo no está disponible",
                     "abro Pronóstico", "veo el pronóstico por promedio móvil y un aviso de qué método se usó"),
                ],
                "Req. 3.0 · OE3 · EDT 1.5.3, 1.5.5", "Must", 5, "Sprint B", ["backend", "frontend", "ml"],
            ),
        ],
    ),
    Epica(
        "EP-07",
        "Recomendaciones de abastecimiento y alertas",
        "Recomendación explicable de cuánto y cuándo comprar, cruzando el pronóstico con las existencias, la "
        "disponibilidad y los tiempos de reposición, y alertas de stock bajo.",
        "OE3 · Requisito 3.2 · EDT 1.5.4, 1.5.5",
        "Mitiga los quiebres de stock. La decisión final, incluido el proveedor, es siempre del tostador.",
        [
            Historia(
                "HU-21", "Recibir una recomendación de cuánto y cuándo comprar", TOSTADOR,
                "recibir una recomendación de la cantidad y la fecha de mi próxima compra",
                "comprar a tiempo sin quedarme sin café ni sobreabastecerme",
                [
                    ("Cálculo", "que tengo existencias, un pronóstico semanal y un plazo de entrega del proveedor",
                     "abro Recomendaciones",
                     "veo la fecha límite de compra (cuando las existencias proyectadas no cubran el consumo durante el plazo de entrega) "
                     "y la cantidad sugerida (consumo pronosticado del plazo de entrega + semanas de cobertura - existencias), redondeada al mínimo de compra"),
                    ("Factores visibles", "que veo una recomendación",
                     "abro su detalle", "veo los factores usados: existencias, consumo pronosticado, plazo de entrega, mínimo de compra y método de pronóstico"),
                    ("Sin recomendación de proveedor", "que tengo varios proveedores con lotes disponibles",
                     "veo la recomendación", "el sistema no recomienda ni selecciona un proveedor"),
                ],
                "Req. 3.2 · OE3 · EDT 1.5.4.1, 1.5.4.2", "Must", 5, "Sprint B", ["backend", "frontend"],
            ),
            Historia(
                "HU-22", "Recibir alertas de stock bajo y próxima compra", TOSTADOR,
                "ver alertas cuando mis existencias estén por debajo de lo que consumiré antes de la próxima entrega",
                "actuar antes de un quiebre de stock",
                [
                    ("Alerta de stock bajo", "que mis existencias cubren menos semanas que el plazo de entrega",
                     "abro mi panel", "veo una alerta destacada con las semanas de cobertura restantes"),
                    ("Sin alerta", "que mis existencias cubren más que el plazo de entrega más una semana",
                     "abro mi panel", "no se muestra la alerta"),
                ],
                "Req. 3.2 · OE3 · EDT 1.5.4.3", "Must", 3, "Sprint B", ["backend", "frontend"],
            ),
        ],
    ),
    Epica(
        "EP-08",
        "Comparación de lotes y desempeño de proveedores",
        "Comparación de lotes de proveedores vinculados e historial de cumplimiento, sin recomendar un proveedor.",
        "OE2, OE3 · Requisito 4.0 · EDT 1.4.4.6, 1.4.5.3",
        "Pedido en las entrevistas 1 y 3. Queda fuera del MVP por tiempo (backlog de mejoras, EDT 1.8.4).",
        [
            Historia(
                "HU-23", "Comparar lotes de mis proveedores vinculados", TOSTADOR,
                "comparar lado a lado lotes de distintos proveedores por características, precio y disponibilidad",
                "elegir con información objetiva",
                [
                    ("Comparación", "que selecciono de 2 a 4 lotes",
                     "hago clic en \"Comparar\"", "veo una tabla con sus atributos alineados, sin un \"recomendado\""),
                ],
                "Req. 4.0 · OE2 · EDT 1.4.4.6", "Should", 5, "Backlog futuro", ["frontend", "backend"],
            ),
            Historia(
                "HU-24", "Ver el cumplimiento histórico de un proveedor", TOSTADOR,
                "ver qué porcentaje de lo acordado me entregó cada proveedor y con qué puntualidad",
                "evaluar la confiabilidad de mis proveedores",
                [
                    ("Indicador", "que tengo compras recibidas de un proveedor",
                     "abro su ficha", "veo el % de kilos recibidos vs acordados y el % de entregas a tiempo"),
                ],
                "Req. 4.0 · OE3 · EDT 1.4.5.3", "Could", 3, "Backlog futuro", ["backend", "frontend"],
            ),
        ],
    ),
]


# --------------------------------------------------------------------------- formato


def cuerpo_historia(h: Historia, epica: Epica, epica_num: int | None = None) -> str:
    ref = f"#{epica_num} " if epica_num else ""
    criterios = "\n\n".join(
        f"**Escenario {i}: {esc}**\n- **Dado** {dado}\n- **Cuando** {cuando}\n- **Entonces** {entonces}"
        for i, (esc, dado, cuando, entonces) in enumerate(h.criterios, 1)
    )
    return (
        f"### Épica\n{ref}{epica.id}: {epica.titulo}\n\n"
        f"### Historia\n**Como** {h.como}\n**quiero** {h.quiero}\n**para** {h.para}\n\n"
        f"### Criterios de aceptación (Gherkin)\n{criterios}\n\n"
        f"### Trazabilidad\n{h.trazabilidad}\n\n"
        f"### Prioridad (MoSCoW)\n{h.prioridad}\n\n"
        f"### Story points\n{h.puntos}\n\n"
        f"### Definition of Ready\n"
        f"- [x] Tiene criterios de aceptación verificables\n"
        f"- [x] Está estimada y priorizada por el Product Owner\n"
        f"- [ ] El contrato de API / diseño de pantalla está definido\n"
        f"- [ ] No tiene dependencias bloqueantes\n"
        f"- [x] Tiene trazabilidad a un requisito, objetivo específico y paquete de la EDT\n"
    )


def cuerpo_epica(e: Epica) -> str:
    lista = "\n".join(f"- {h.id}: {h.titulo} ({h.prioridad}, {h.puntos} pts, {h.sprint})" for h in e.historias)
    return (
        f"### Descripción\n{e.descripcion}\n\n"
        f"### Objetivo específico y paquete EDT\n{e.objetivo}\n\n"
        f"### Valor para el usuario\n{e.valor}\n\n"
        f"### Historias de usuario\n{lista}\n"
    )


def generar_md() -> str:
    todas = [(e, h) for e in EPICAS for h in e.historias]
    mvp = [h for _, h in todas if h.sprint != "Backlog futuro"]
    lineas = [
        "# Product Backlog — MVP de Origin Link",
        "",
        "> Generado por `scripts/backlog.py md`. Para cambiar el backlog, editar ese archivo y regenerar.",
        "",
        "Fuentes: matriz de trazabilidad (Project Charter 4.1), matriz de necesidades por actor (Anexo 5) y EDT.",
        "",
        "## Resumen",
        "",
        f"- **{len(EPICAS)} épicas**, **{sum(h.tipo == 'historia' for _, h in todas)} historias de usuario** y "
        f"**{sum(h.tipo != 'historia' for _, h in todas)} tarea técnica** (TT: habilitadores sin usuario final).",
        f"- **MVP:** {len(mvp)} historias, {sum(h.puntos for h in mvp)} story points.",
    ]
    for s, (fecha, objetivo) in SPRINTS.items():
        hs = [h for _, h in todas if h.sprint == s]
        lineas.append(f"- **{s}** ({len(hs)} historias, {sum(h.puntos for h in hs)} pts): {objetivo}.")
    lineas += [
        "",
        "## Flujo del MVP (User Story Mapping simplificado)",
        "",
        "| Actividad del usuario | Historias (Sprint A) | Historias (Sprint B) | Fuera del MVP |",
        "|---|---|---|---|",
    ]
    for e in EPICAS:
        cols = {s: ", ".join(h.id for h in e.historias if h.sprint == s) or "—" for s in SPRINTS}
        lineas.append(f"| {e.id} {e.titulo} | {cols['Sprint A']} | {cols['Sprint B']} | {cols['Backlog futuro']} |")
    lineas += [
        "",
        "## Product Backlog priorizado",
        "",
        "| ID | Historia | Épica | Prioridad | Pts | Sprint | Área | Trazabilidad |",
        "|---|---|---|---|---|---|---|---|",
    ]
    orden = {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}
    orden_sprint = {s: i for i, s in enumerate(SPRINTS)}
    for e, h in sorted(todas, key=lambda x: (orden_sprint[x[1].sprint], orden[x[1].prioridad], x[1].id)):
        lineas.append(
            f"| {h.id} | {h.titulo} | {e.id} | {h.prioridad} | {h.puntos} | {h.sprint} | "
            f"{', '.join(h.area)} | {h.trazabilidad} |"
        )
    lineas += [
        "",
        "## Definition of Ready (DoR)",
        "",
        "Una historia entra a un sprint solo si:",
        "",
        "1. Tiene el formato Como / Quiero / Para y criterios de aceptación verificables en Gherkin.",
        "2. Está estimada en story points y priorizada por el Product Owner.",
        "3. Tiene definido el contrato de API y/o el diseño de la pantalla.",
        "4. No tiene dependencias bloqueantes con historias no terminadas.",
        "5. Tiene trazabilidad a un requisito, un objetivo específico y un paquete de la EDT.",
        "",
        "## Definition of Done (DoD)",
        "",
        "Una historia está terminada solo si:",
        "",
        "1. Cumple todos sus criterios de aceptación.",
        "2. Tiene pruebas escritas antes del código (TDD) y el CI está en verde.",
        "3. Fue revisada y probada por otro integrante (prueba cruzada).",
        "4. Está unida a `develop` mediante un PR con `Closes #<issue>`.",
        "5. Se desplegó en el ambiente de validación sin errores.",
        "",
        "## Detalle de épicas e historias",
        "",
    ]
    for e in EPICAS:
        lineas += [f"### {e.id}: {e.titulo}", "", cuerpo_epica(e).replace("### ", "#### "), ""]
        for h in e.historias:
            lineas += [f"#### {h.id}: {h.titulo}", "", cuerpo_historia(h, e).replace("### ", "##### "), ""]
    return "\n".join(lineas).rstrip() + "\n"


# --------------------------------------------------------------------------- GitHub


def gh(args: list[str], dry: bool, salida: bool = False) -> str:
    if dry:
        print("  gh " + " ".join(a if " " not in a else repr(a) for a in args[:6]) + (" ..." if len(args) > 6 else ""))
        return "https://github.com/" + REPO + "/issues/0"
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"Error en gh {' '.join(args[:3])}:\n{r.stderr}")
    return r.stdout.strip() if salida else ""


def crear_issue(titulo: str, cuerpo: str, labels: list[str], milestone: str | None, dry: bool) -> str:
    args = ["issue", "create", "--repo", REPO, "--title", titulo, "--body", cuerpo]
    for lb in labels:
        args += ["--label", lb]
    if milestone:
        args += ["--milestone", milestone]
    return gh(args, dry, salida=True)


def numero(url: str) -> int:
    return int(url.rstrip("/").rsplit("/", 1)[-1])


def vincular_subissue(epica_url: str, hu_url: str, dry: bool) -> None:
    """Agrega la historia como sub-issue de la épica (API de sub-issues de GitHub)."""
    if dry:
        return
    hu_id = gh(["api", f"repos/{REPO}/issues/{numero(hu_url)}", "--jq", ".id"], dry, salida=True)
    r = subprocess.run(
        ["gh", "api", "-X", "POST", f"repos/{REPO}/issues/{numero(epica_url)}/sub_issues",
         "-F", f"sub_issue_id={hu_id}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        print(f"  (aviso) no se pudo vincular como sub-issue: {r.stderr.strip()[:120]}")


def etiqueta(h: Historia) -> str:
    return "historia-de-usuario" if h.tipo == "historia" else "tarea-tecnica"


def issues_existentes(dry: bool) -> dict[str, int]:
    """Título → número de los issues que ya existen en el repo."""
    if dry:
        return {}
    datos = gh(["issue", "list", "--repo", REPO, "--state", "all", "--limit", "500", "--json", "title,number"], dry, True)
    return {i["title"]: i["number"] for i in json.loads(datos)}


def conservar_marcas(nuevo: str, actual: str) -> str:
    """Marca en el cuerpo nuevo las casillas que el equipo ya marcó en el issue."""
    marcadas = {ln.strip()[6:] for ln in actual.splitlines() if ln.strip().lower().startswith("- [x] ")}
    lineas = []
    for ln in nuevo.splitlines():
        if ln.startswith("- [ ] ") and ln[6:] in marcadas:
            ln = "- [x] " + ln[6:]
        lineas.append(ln)
    return "\n".join(lineas) + ("\n" if nuevo.endswith("\n") else "")


def actualizar_issues(dry: bool) -> None:
    """Actualiza el cuerpo de épicas e historias existentes (ej. nuevo ítem de la DoR o nuevos criterios).

    Necesita `gh` autenticado incluso en --dry-run, porque compara con lo que hay en GitHub.
    """
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        raise SystemExit("Primero ejecuta: gh auth login")
    existentes = issues_existentes(False)
    cambios = 0

    def revisar(num: int, nuevo: str, etiqueta_issue: str) -> None:
        nonlocal cambios
        actual = json.loads(gh(["issue", "view", str(num), "--repo", REPO, "--json", "body"], False, True))["body"]
        nuevo = conservar_marcas(nuevo, actual)
        if nuevo.strip() == actual.strip():
            return
        cambios += 1
        print(f"  #{num} {etiqueta_issue}: {'se actualizaría' if dry else 'actualizado'}")
        if not dry:
            gh(["issue", "edit", str(num), "--repo", REPO, "--body", nuevo], False)

    for e in EPICAS:
        num_epica = existentes.get(f"{e.id}: {e.titulo}")
        if num_epica:
            revisar(num_epica, cuerpo_epica(e), e.id)
        for h in e.historias:
            num = existentes.get(f"{h.id}: {h.titulo}")
            if not num:
                print(f"  {h.id}: no existe todavía (créalo con: python scripts/backlog.py issues)")
                continue
            revisar(num, cuerpo_historia(h, e, num_epica), h.id)
    print(f"{cambios} issues {'por actualizar (simulación)' if dry else 'actualizados'}.")


def cargar_issues(dry: bool, proyecto: int | None) -> None:
    if not dry and subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        raise SystemExit("Primero ejecuta: gh auth login")

    existentes = issues_existentes(dry)

    print("Labels...")
    labels = {
        "epica": "5319e7", "historia-de-usuario": "1d76db", "defecto": "d73a4a",
        "Must": "b60205", "Should": "fbca04", "Could": "0e8a16", "Won't": "cccccc",
        "frontend": "c5def5", "backend": "bfd4f2", "ml": "d4c5f9", "tarea-tecnica": "006b75",
    }
    for nombre, color in labels.items():
        gh(["label", "create", nombre, "--repo", REPO, "--color", color, "--force"], dry)

    print("Milestones (sprints)...")
    actuales = set()
    if not dry:
        actuales = {m["title"] for m in json.loads(gh(["api", f"repos/{REPO}/milestones?state=all"], dry, True))}
    for titulo, (fecha, desc) in SPRINTS.items():
        if titulo in actuales:
            continue
        args = ["api", f"repos/{REPO}/milestones", "-f", f"title={titulo}", "-f", f"description={desc}"]
        if fecha:
            args += ["-f", f"due_on={fecha}"]
        gh(args, dry)

    urls: list[str] = []
    for e in EPICAS:
        titulo_e = f"{e.id}: {e.titulo}"
        print(titulo_e)
        if titulo_e in existentes:
            print("  ya existe")
            epica_url = f"https://github.com/{REPO}/issues/{existentes[titulo_e]}"
        else:
            epica_url = crear_issue(titulo_e, cuerpo_epica(e), ["epica"], None, dry)
            urls.append(epica_url)
        for h in e.historias:
            titulo_h = f"{h.id}: {h.titulo}"
            if titulo_h in existentes:
                continue
            cuerpo = cuerpo_historia(h, e, numero(epica_url) if epica_url and not dry else None)
            url = crear_issue(titulo_h, cuerpo, [etiqueta(h), h.prioridad, *h.area], h.sprint, dry)
            urls.append(url)
            if epica_url:
                vincular_subissue(epica_url, url, dry)
            print(f"  {titulo_h} -> {url}")

    if proyecto:
        print(f"Agregando {len(urls)} issues al Project #{proyecto}...")
        for url in urls:
            gh(["project", "item-add", str(proyecto), "--owner", ORG, "--url", url], dry)
    print("Listo." if not dry else "Simulación terminada: no se creó nada.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("md")
    pi = sub.add_parser("issues")
    pi.add_argument("--dry-run", action="store_true")
    pi.add_argument("--proyecto", type=int, help="Número del GitHub Project de la organización")
    pa = sub.add_parser("actualizar")
    pa.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.cmd == "md":
        destino = Path(__file__).resolve().parent.parent / "docs" / "backlog" / "product-backlog.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(generar_md(), encoding="utf-8")
        print(f"Generado {destino}")
    elif a.cmd == "actualizar":
        actualizar_issues(a.dry_run)
    else:
        cargar_issues(a.dry_run, a.proyecto)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
