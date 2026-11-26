# Contrato de la API — MVP de Origin Link

Responsables: Victor Cruz (backend) y Christian Inga (frontend). Aprobación: Luciana Choquehuanca.
Schemas de referencia (fuente de verdad): `backend/app/schemas/`. Tipos para el frontend:
`frontend/src/lib/types.ts`. Con la API levantada, la documentación interactiva está en `/docs` (Swagger).

> El backend implementa exactamente estas rutas y formas; el frontend puede avanzar en paralelo con datos
> simulados que respeten estos tipos. Un cambio al contrato se acuerda entre ambos y se actualiza aquí,
> en los schemas y en `types.ts` en el mismo PR.

## Convenciones

| Tema | Regla |
|---|---|
| URL base | `{API_URL}/api/v1` |
| Autenticación | JWT en el header `Authorization: Bearer <access_token>` (todas las rutas salvo registro, login e info de invitación). Expira en 8 h |
| Cerrar sesión (HU-02) | El frontend borra el token; no hay endpoint |
| Formato | JSON. Fechas `YYYY-MM-DD`, fecha-hora ISO 8601 con zona. Kg y soles como **número** (`28.5`) |
| Roles | 🟤 = solo tostador · 🟢 = solo cooperativa · ⚪ = ambos |
| Errores | `{"detail": "mensaje para el usuario"}`. Validación (422): formato estándar de FastAPI |

| Código | Cuándo |
|---|---|
| 200 / 201 | OK / creado |
| 204 | Eliminado o acción sin contenido |
| 400 | Regla de negocio (ej. consumo mayor a las existencias) |
| 401 | Sin token o token vencido → el frontend envía al login |
| 403 | Rol incorrecto o recurso de otra organización (HU-04) |
| 404 | No existe **o** no es visible para el usuario |
| 409 | Duplicado (ej. correo ya registrado) |
| 422 | Datos con formato inválido |

## Resumen de endpoints

| HU | Método | Ruta | Rol | Body | Respuesta |
|---|---|---|---|---|---|
| HU-01 | POST | `/auth/registro` | público | `RegistroTostadorIn` | 201 `TokenOut` |
| HU-02 | POST | `/auth/login` | público | `LoginIn` | 200 `TokenOut` |
| HU-02 | GET | `/auth/me` | ⚪ | — | 200 `UsuarioOut` |
| HU-03 | GET | `/invitaciones/{token}` | público | — | 200 `InvitacionInfoOut` |
| HU-03 | POST | `/auth/registro-invitacion` | público | `RegistroPorInvitacionIn` | 201 `TokenOut` |
| HU-03 | POST | `/invitaciones/{token}/aceptar` | 🟢 | — | 200 `VinculoOut` |
| HU-05 | GET | `/proveedores` | 🟤 | — | 200 `ProveedorOut[]` |
| HU-05 | POST | `/proveedores` | 🟤 | `ProveedorIn` | 201 `ProveedorOut` |
| HU-05 | GET | `/proveedores/{id}` | 🟤 | — | 200 `ProveedorOut` |
| HU-05 | PATCH | `/proveedores/{id}` | 🟤 | `ProveedorUpdate` | 200 `ProveedorOut` |
| HU-06 | POST | `/proveedores/{id}/invitaciones` | 🟤 | — | 201 `InvitacionOut` |
| HU-07 | GET | `/vinculos` | 🟢 | — | 200 `VinculoOut[]` |
| HU-08 | POST | `/lotes` | 🟢 (🟤 con `proveedor_id`, HU-11) | `LoteIn` | 201 `LoteOut` |
| HU-09 | GET | `/lotes?proveedor_id=&proceso=&disponibles=true` | ⚪ | — | 200 `LoteOut[]` |
| HU-09 | GET | `/lotes/{id}` | ⚪ | — | 200 `LoteOut` |
| HU-10 | PATCH | `/lotes/{id}/disponibilidad` | 🟢 (🟤 en lotes propios) | `DisponibilidadUpdate` | 200 `LoteOut` |
| HU-13 | POST | `/compras` | 🟤 | `CompraIn` | 201 `CompraOut` |
| HU-13 | GET | `/compras?estado=&proveedor_id=` | 🟤 | — | 200 `CompraOut[]` |
| HU-14 | POST | `/compras/{id}/recepcion` | 🟤 | `RecepcionIn` | 201 `CompraOut` |
| HU-15 | GET | `/proveedores/{id}/compras` | 🟤 | — | 200 `CompraOut[]` |
| HU-16 | POST | `/movimientos` | 🟤 | `MovimientoIn` | 201 `MovimientoOut` |
| HU-16 | GET | `/movimientos?lote_id=&tipo=&desde=&hasta=` | 🟤 | — | 200 `MovimientoOut[]` |
| HU-17 | GET | `/existencias` | 🟤 | — | 200 `ExistenciasOut` |
| HU-18 | POST | `/consumo-historico/importar` | 🟤 | `multipart/form-data` (`archivo`: .csv o .xlsx) | 200 `ImportacionOut` |
| HU-20 | GET | `/pronostico?semanas=4` | 🟤 | — | 200 `PronosticoOut` |
| HU-21 | GET | `/recomendaciones?plazo_entrega_dias=&cantidad_minima_kg=` | 🟤 | — (los parámetros simulan otro lote) | 200 `RecomendacionOut` |
| HU-22 | GET | `/alertas` | 🟤 | — | 200 `AlertaOut[]` |
| HU-07 (apoyo al frontend) | GET | `/pedidos-recibidos` | 🟤 | — (cooperativa) | 200 `PedidoRecibidoOut[]` |

Las rutas de HU-18 a HU-22 están implementadas. `/pedidos-recibidos` y los campos marcados en «Aclaraciones del Sprint B y del frontend» existen para que la interfaz funcione con el API real.

## Detalle por módulo

### EP-01 Identidad y acceso

**POST `/auth/registro`** (HU-01)
```json
{ "empresa": "Tostaduría Raúl", "ruc": "20123456789", "nombre": "Raúl Tello",
  "email": "raul@cafe.pe", "password": "********" }
```
201 →
```json
{ "access_token": "eyJ...", "token_type": "bearer",
  "usuario": { "id": 1, "nombre": "Raúl Tello", "email": "raul@cafe.pe",
    "organizacion": { "id": 1, "tipo": "TOSTADOR", "nombre": "Tostaduría Raúl", "ruc": "20123456789", "region": null } } }
```
409 `{"detail": "Ya existe una cuenta con este correo"}`

**POST `/auth/login`** (HU-02) → 200 `TokenOut` · 401 `{"detail": "Correo o contraseña incorrectos"}`

**GET `/invitaciones/{token}`** (HU-03, pantalla pública de registro de la cooperativa)
```json
{ "tostador": "Tostaduría Raúl", "proveedor": "Coop. Jaén", "vigente": true, "expira_en": "2026-11-26T18:00:00-05:00" }
```
404 si el token no existe. Si venció o ya se usó: `vigente: false`.

**POST `/auth/registro-invitacion`** (HU-03): como el registro, más `token` y `region`. Crea la organización
PROVEEDOR, la vincula (`estado_vinculo = VINCULADO`) y marca la invitación como usada.
400 `{"detail": "Invitación no válida"}` si venció o ya se usó.

**POST `/invitaciones/{token}/aceptar`** (HU-03): para una cooperativa que ya tiene cuenta y recibe la
invitación de otro tostador.

**HU-04 (regla transversal):** cada consulta filtra por la organización del token. Un tostador solo ve sus
proveedores, compras, movimientos y existencias, y los lotes de cooperativas **vinculadas** o de su propio
directorio. Una cooperativa solo ve sus lotes y sus vínculos. Si no corresponde → 404 (no revela que existe)
o 403 si el rol no puede usar la ruta.

### EP-02 Proveedores y relaciones privadas

**POST `/proveedores`** (HU-05)
```json
{ "nombre": "Coop. Jaén", "region": "Cajamarca", "contacto_nombre": "Ana Pérez",
  "contacto_telefono": "987654321", "contacto_email": "ana@coopjaen.pe" }
```
201 → `ProveedorOut` con `"estado_vinculo": "SIN_VINCULAR"`.

**POST `/proveedores/{id}/invitaciones`** (HU-06): genera un token aleatorio (`secrets.token_urlsafe(32)`),
vigencia de 7 días, y pasa el proveedor a `INVITADO`.
```json
{ "token": "x7Gk...", "url": "https://<frontend>/invitacion/x7Gk...", "expira_en": "2026-11-26T18:00:00-05:00" }
```
409 si el proveedor ya está `VINCULADO`.

**GET `/vinculos`** (HU-07, cooperativa)
```json
[ { "tostador_id": 1, "tostador": "Tostaduría Raúl", "vinculado_desde": "2026-11-19T10:00:00-05:00" } ]
```
La vista del tostador (HU-07) es `GET /proveedores`, que ya trae `estado_vinculo`.

### EP-03 Gestión colaborativa de lotes

**POST `/lotes`** (HU-08)
```json
{ "codigo": "JAEN-2026-07", "region": "Cajamarca - Jaén", "finca": "El Mirador", "variedad": "Caturra",
  "proceso": "LAVADO", "cosecha": "2026", "altitud_msnm": 1650,
  "caracteristicas": "Notas a chocolate y panela. Puntaje declarado 84",
  "cantidad_disponible_kg": 200, "precio_kg": 28.5, "cantidad_minima_kg": 30, "plazo_entrega_dias": 10 }
```
201 → `LoteOut`:
```json
{ "id": 7, "proveedor_nombre": "Coop. Jaén", "registrado_por_tostador": false, "codigo": "JAEN-2026-07",
  "region": "Cajamarca - Jaén", "finca": "El Mirador", "variedad": "Caturra", "proceso": "LAVADO",
  "cosecha": "2026", "altitud_msnm": 1650, "caracteristicas": "...", "cantidad_disponible_kg": 200,
  "precio_kg": 28.5, "cantidad_minima_kg": 30, "plazo_entrega_dias": 10, "agotado": false,
  "actualizado_en": "2026-11-19T10:00:00-05:00" }
```
HU-11: el tostador envía además `"proveedor_id": 3` (un proveedor de su directorio).

**PATCH `/lotes/{id}/disponibilidad`** (HU-10): `{ "cantidad_disponible_kg": 0 }` → `LoteOut` con `"agotado": true`.

### EP-04 Compras y recepciones

**POST `/compras`** (HU-13)
```json
{ "lote_id": 7, "cantidad_kg": 60, "precio_kg": 28.5, "fecha_compra": "2026-11-19",
  "fecha_entrega_acordada": "2026-11-29", "observaciones": null }
```
201 → `CompraOut` con `"estado": "PENDIENTE"`, `"total": 1710`, `"recepcion": null`. Si la cantidad supera
la disponible del lote, igual se registra y `"advertencia": "La cantidad supera lo disponible en el lote"`.

**POST `/compras/{id}/recepcion`** (HU-14)
```json
{ "fecha_recepcion": "2026-11-29", "cantidad_recibida_kg": 55, "observaciones": "Un saco con humedad" }
```
201 → `CompraOut` con `"estado": "RECIBIDA"` y
`"recepcion": { "id": 3, "fecha_recepcion": "2026-11-29", "cantidad_recibida_kg": 55, "diferencia_kg": -5, ... }`.
Crea el movimiento `ENTRADA` de 55 kg. 409 si la compra ya fue recibida.

### EP-05 Inventario y existencias

**POST `/movimientos`** (HU-16)
```json
{ "lote_id": 7, "tipo": "CONSUMO", "cantidad_kg": 8, "fecha": "2026-11-30", "motivo": null }
```
Ajuste: `{ "lote_id": 7, "tipo": "AJUSTE", "cantidad_kg": -1.5, "fecha": "2026-11-30", "motivo": "Conteo físico" }`.
400 `{"detail": "El consumo supera las existencias del lote (5 kg)"}`. 422 si es `ENTRADA` o ajuste sin motivo.

**GET `/existencias`** (HU-17)
```json
{ "total_kg": 46,
  "lotes": [ { "lote_id": 7, "lote_codigo": "JAEN-2026-07", "proveedor_nombre": "Coop. Jaén", "existencias_kg": 46 } ] }
```

**POST `/consumo-historico/importar`** (HU-18): archivo con columnas `fecha` y `kg_consumidos`
(diario o semanal; se agrega por semana, lunes). Todo o nada:
```json
{ "semanas_importadas": 52, "desde": "2025-11-17", "hasta": "2026-11-09", "errores": [] }
```
Con errores: `"semanas_importadas": 0, "errores": [{"fila": 14, "error": "kg_consumidos negativo"}]`.

### EP-06 y EP-07 Pronóstico, recomendaciones y alertas (Sprint B, preliminar)

**GET `/pronostico`** (HU-20)
```json
{ "metodo": "TCN", "motivo_metodo": null,
  "historial": [ { "semana": "2026-11-02", "kg": 7.0 } ],
  "pronostico": [ { "semana": "2026-11-23", "kg": 7.4 }, { "semana": "2026-11-30", "kg": 7.6 } ],
  "mape_referencia": 12.3 }
```

**GET `/recomendaciones`** (HU-21)
```json
{ "fecha_limite_compra": "2026-11-26", "cantidad_sugerida_kg": 30, "semanas_cobertura_actual": 2.1,
  "factores": { "existencias_kg": 15.5, "consumo_semanal_pronosticado_kg": [ { "semana": "2026-11-23", "kg": 7.4 } ],
    "plazo_entrega_dias": 10, "semanas_cobertura": 2, "cantidad_minima_kg": 30, "metodo_pronostico": "TCN" },
  "explicacion": "Tus 15.5 kg alcanzan ~2.1 semanas. El proveedor tarda 10 días..." }
```
Cálculo (criterios de HU-21): fecha límite = día en que las existencias proyectadas ya no cubren el consumo
pronosticado durante el plazo de entrega; cantidad = consumo pronosticado (plazo de entrega + semanas de
cobertura) − existencias, redondeada hacia arriba al mínimo de compra. No elige proveedor: usa el plazo de
entrega y el mínimo de compra del último lote comprado (o los valores por defecto 7 días y 0 kg).

**GET `/alertas`** (HU-22)
```json
[ { "tipo": "STOCK_BAJO", "mensaje": "Tus existencias cubren 1.2 semanas y la entrega tarda 10 días",
    "semanas_cobertura_restantes": 1.2, "fecha_limite_compra": "2026-11-20" } ]
```

## Aclaraciones de la implementación (Sprint A)

Reglas que el código aplica y que el contrato no detallaba. No cambian ninguna ruta ni forma de respuesta.

| Tema | Regla |
|---|---|
| HU-04 | Rol incorrecto → 403. Recurso de otra organización o no visible (proveedor, compra, lote) → 404. Sin token → 401. Lo verifica `tests/test_control_acceso_hu04.py` sobre todas las rutas |
| HU-05 | El nombre del proveedor se guarda sin espacios sobrantes y debe tener al menos 2 caracteres; también en `PATCH` (no admite `null`) |
| HU-06 | Una sola invitación vigente por proveedor: al generar otra, las anteriores sin usar vencen. El enlace usa la variable `FRONTEND_URL` |
| HU-07 | `vinculado_desde` es la fecha de uso de la invitación; si el vínculo no vino de una invitación, la última actualización de la ficha |
| HU-08 / HU-11 | `POST /lotes`: la cooperativa debe estar vinculada con al menos un tostador (400) y no envía `proveedor_id` (400). El tostador debe enviar `proveedor_id` (400), de su propio directorio (404 si es de otro) y no vinculado (409: ese proveedor publica sus propios lotes) |
| HU-09 | El tostador ve los lotes **publicados** de cooperativas vinculadas con él y los de su directorio; la cooperativa ve los suyos, publicados o no |
| HU-10 | `PATCH /lotes/{id}/disponibilidad`: lote no visible → 404; visible pero ajeno → 403; los campos enviados no pueden ser `null` (422) |
| HU-13 | La compra no descuenta la disponibilidad del lote; la actualiza la cooperativa (HU-10) |
| HU-14 | `cantidad_recibida_kg` debe ser mayor que 0 (422). Recibir una compra ya recibida o anulada → 409 |
| HU-16 | Una salida (consumo, merma o ajuste negativo) que deje las existencias de un lote bajo 0 → 400 y no se registra |
| HU-17 | Las existencias de los lotes consumidos por completo no aparecen en la lista |

## Aclaraciones del Sprint B y del frontend

| Tema | Regla |
|---|---|
| Números en JSON | Kilos y soles se serializan como número (no como texto). Internamente son `Decimal` |
| Sesión | `JWT_SECRET_KEY` (mínimo 32 caracteres) es obligatoria: sin ella el login responde 500 |
| `LoteOut.proveedor_id` | Para el tostador es el id de su ficha de proveedor, también en los lotes publicados por una cooperativa vinculada. `LoteIn.cantidad_minima_kg` es opcional (0 por defecto) |
| `ProveedorOut.invitacion_vigente` | `{ "token", "expira_en" }` de la última invitación sin usar ni vencer, o `null`. Con el token el frontend arma el enlace `/invitacion?token=…` |
| `GET /pedidos-recibidos` | Solo cooperativa. Compras de las tostadoras vinculadas sobre sus lotes, más recientes primero: `id, tostador, lote_id, lote_codigo, cantidad_kg, recibido_kg, fecha_compra, fecha_entrega_acordada, estado` |
| `GET /recomendaciones` | `plazo_entrega_dias` (0–180) y `cantidad_minima_kg` (≥ 0) calculan la recomendación con las condiciones de otro lote sin guardar nada. La respuesta incluye `dias_cobertura_actual` |
| Historial semanal | Consumo importado + movimientos de consumo, por semana (lunes). Las semanas sin dato valen 0 y **la semana en curso se excluye** por estar incompleta. El pronóstico empieza el lunes siguiente a la última semana completa |
| Método de pronóstico | Usa la TCN global si existe `ml/models/tcn_global.pt` (ruta configurable con `MODEL_PATH`, carpeta del código con `ML_PATH`), están instalados `torch`, `numpy` y `pandas` y el historial alcanza el mínimo del modelo. Si no, promedio móvil de 4 semanas y `motivo_metodo` dice por qué |
