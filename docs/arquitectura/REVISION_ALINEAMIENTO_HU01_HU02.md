# Revisión de alineamiento — Identidad y acceso (HU-01 / HU-02)

**Estado:** propuesta técnica, pendiente de revisión cruzada y PR #35 aprobado.
**Base:** Project Charter — EQUIPO 3, tercer avance (12/11/2026), y el repositorio `develop` entregado por el equipo.
**Dependencia:** PR #35 `docs/modelo-datos-api` (modelos, migración, schemas y contrato).

## Jerarquía de decisiones y límites

1. El **Project Charter**, los criterios de aceptación y exclusiones definen lo que necesita el producto.
2. Los ADR, el C4, la estructura `backend/app` y los contratos existentes determinan **cómo** se integra.
3. Las técnicas de seguridad y arquitectura se incorporan solo cuando complementan lo anterior y se justifican.
4. Si hay contradicciones, se **registra una decisión**, no se sustituyen hechos silenciosamente.

## Trazabilidad

| Requisito / referencia | Implementación | Evidencia prevista | Estado |
|---|---|---|---|
| Charter §12.1.4, HU-01 Esc. 01: registro / rol tostador / panel | `Registro.tsx`, `auth.py`, `auth_service.py`, `Inicio.tsx` | test API registro 201 y test UI navegación | Implementado, integración pendiente |
| Charter §12.1.4, HU-01 Esc. 02: correo duplicado | UNIQUE en PR #35; respuesta 409 y mensaje contractual | test API duplicado; test UI error | Implementado, integración pendiente |
| Charter §12.1.4, HU-02 Esc. 01: login por rol | JWT 8h, `AuthContext`, `Inicio` por rol y menú diferenciado | test API login, test UI cooperativa | Implementado, integración pendiente |
| Charter §12.1.4, HU-02 Esc. 02: fallo genérico | `auth_service.py`, respuesta 401 idéntica | tests API/UI | Implementado, integración pendiente |
| Charter §12.1.4, HU-02 Esc. 03: logout bloquea acceso | token en sessionStorage, salida a login, `ProtectedRoute` | test UI logout | Implementado, integración pendiente |
| Charter §12.1.3 DoD: TDD, CI, pruebas cruzadas, PR y despliegue | tests en repositorio; pipelines GitHub Actions existentes | reporte CI, revisión de integrante, URL de validación | **PENDIENTE** |
| Charter §4.2.1 ARQ-01: privacidad y permisos | autenticación en `/me`; guardia visual de rol | HU-04: políticas de autorización de cada recurso | **PENDIENTE HU-04** |
| Charter §4.2.1 ARQ-02: transacciones | usuario+organización insertados en una transacción | prueba de integración con BD | Implementado, integración pendiente |

## Estructura respetada

- `backend/app/api/routes`: interfaz HTTP de identidad
- `backend/app/services`: registro/login y límites de transacción
- `backend/app/core`: hash/firmas de autenticación y configuración de secretos
- `backend/app/models`, `backend/app/schemas`, `backend/alembic`: **dependen de PR #35**, no se duplican
- `frontend/src/pages`, `components`, `auth`, `lib`: navegación, formularios, token, cliente HTTP
- `docs/adr`: justificación de decisiones, sin modificar decisiones antiguas

**Monolito modular:** la API FastAPI se despliega como una unidad, con módulos identificables por dominio
(identidad, proveedores, lotes, compras, inventario y pronóstico). Los directorios actuales de rutas,
servicios y modelos se conservan. Se aplica separación por capas dentro de los módulos sin convertir
el backend en una red de microservicios ni imponer DDD táctico sin necesidad.

## Discrepancias que exigen seguimiento

- El Project Charter §3.9 describe infraestructura AWS EC2/Render/Vercel y costes asociados; el ADR-0002,
  C4 y guía del repositorio definen GCP Cloud Run + Firebase Hosting + Neon. **No se cambia presupuesto ni
  la documentación aprobada sin acuerdo del PM.** Se plantea registrar la actualización de línea base.
- El Charter histórico indica H04 aprobado (15/10) y H09 desplegado (14/11), pero el snapshot de código
  revisado carece aún de modelos y endpoints. Los hitos documentales **no son evidencia de despliegue
  del código de este paquete**. Requiere verificación de GitHub y ambiente real.
- El modelo `lotes` del PR #35 y la relación recepción/movimiento requieren resolver las observaciones
  arquitectónicas ya enviadas al PR antes de incorporarse.
- El contrato indica logout cliente sin endpoint; un JWT emitido puede seguir vigente hasta su expiración.
  Este comportamiento es **una limitación conocida**, no una revocación del servidor.

## Puertas de calidad antes del merge a develop

1. PR #35 corregido, revisión aprobada y migración aplicada en BD de prueba PostgreSQL 16.
2. Ejecutar `ruff check .`, `ruff format --check .`, `pytest` desde `backend/`.
3. Ejecutar `npm ci`, `npm run lint`, `npm test -- --runInBand`, `npm run build` desde `frontend/`.
4. Validar con pruebas cruzadas de otro integrante HU-01/HU-02 según escenarios Gherkin del Charter.
5. CI verde, PR de feature a `develop` asociado a issues #4/#5; aprobar cambios con PM.
6. Evidencia de despliegue real en ambiente de validación antes de declarar DoD completo.
