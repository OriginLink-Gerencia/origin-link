# H04 — Revisión de arquitectura e integración (corte: 25/11/2026)

**Responsable de arquitectura:** Luciana Choquehuanca.  
**Revisores técnicos previstos:** Christian Inga y Víctor Cruz.  
**Estado:** revisión técnica preparada; **pendiente de aprobación cruzada y validación del despliegue**.

> Este documento distingue implementación, pruebas locales, integración en `develop` y validación en ambiente desplegado. Los resultados reportados corresponden a la rama de trabajo y no acreditan por sí solos el cierre del hito H04.

## 1. Arquitectura y límites

- **Contexto:** tostador y cooperativa colaboran de forma privada en Origin Link; no es un marketplace público.
- **Frontend:** SPA React 18 + TypeScript + Tailwind, con vistas diferenciadas según rol.
- **Backend:** monolito modular FastAPI, con separación entre rutas, servicios, esquemas y ORM.
- **Persistencia:** PostgreSQL gestionado en Neon; SQLite se utiliza únicamente en pruebas automatizadas aisladas.
- **Pronóstico:** el TCN forma parte del diseño objetivo; no se considera integrado ni desplegado por el hecho de figurar en el C4.
- **Despliegue objetivo:** Firebase Hosting (SPA) y Cloud Run (API) con imágenes en Artifact Registry y secretos externos. **Se requiere comprobar las URLs y la ejecución real.**

Los diagramas C4 existentes se mantienen en `docs/arquitectura/README.md`; cualquier diferencia frente al entorno desplegado debe registrarse y resolverse antes de cerrar H04.

## 2. Matriz de trazabilidad técnica (estado al corte)

| Historia / requisito | Implementación identificada | Pruebas / evidencia | Situación |
|---|---|---|---|
| HU-01: alta de tostador | `backend/app/api/routes/auth.py`, `frontend/src/pages/Registro.tsx` | `backend/tests/test_auth_hu01_hu02.py`, `frontend/src/App.test.tsx` | Implementada en rama; PR #39 pendiente |
| HU-02: inicio/cierre de sesión | `auth.py`, `auth_security.py`, `AuthContext.tsx`, `Login.tsx` | Pruebas de API/UI, JWT y cierre cliente | Implementada en rama; PR #39 pendiente |
| HU-03: registro por invitación | `invitaciones.py`, `invitaciones_service.py`, `Invitacion.tsx` | `test_invitaciones_hu03.py`, `test_flujo_integrado.py` | Implementada en rama; PR #41 pendiente |
| HU-04: roles y aislamiento | `api/deps.py`, filtros por organización en `proveedores.py` y `vinculos.py` | `test_seguridad_hu04.py`, pruebas HU-05 y HU-07 | **Cobertura parcial:** compras, inventario y lotes no verificados |
| HU-05: registro de proveedor | `proveedores.py`, `Proveedores.tsx` | `test_proveedores_hu05.py`, `ProveedoresVinculos.test.tsx` | Implementada en rama; revisión con autor PR #40 |
| HU-06: invitar proveedor | `proveedores.py` (ruta de invitación), `Proveedores.tsx` | `test_invitaciones_hu06.py`, prueba integrada | Implementada en rama; revisión pendiente |
| HU-07: ver vínculos | `vinculos.py`, `Vinculos.tsx` | `test_vinculos_hu07.py`, pruebas frontend | Implementada en rama; revisión pendiente |
| ARQ-01: privacidad | JWT, comprobación de rol, pertenencia por organización | Tests 401/403/404 | Cobertura comprobada para rutas presentes; pendiente resto del sistema |
| ARQ-02: integridad transaccional | Registro de organización/usuario y consumo de invitación | `test_invitaciones_hu03.py` y prueba integral | Comprobado en pruebas aisladas; validar en PostgreSQL integrado |

## 3. Atributos de calidad y verificaciones

| Atributo | Escenario verificable | Evidencia existente / pendiente |
|---|---|---|
| Seguridad | Ruta privada sin sesión | Pruebas API: HTTP 401 |
| Autorización | Rol no autorizado consulta recurso ajeno | Pruebas API: HTTP 403/404 según recurso |
| Aislamiento | Tostador B no ve proveedores del tostador A | Pruebas backend HU-05/HU-04 |
| Integridad | Una invitación usada deja de ser vigente | `test_invitaciones_hu03.py` y flujo integrado |
| Usabilidad | Registro y navegación en frontend | Pruebas Jest existentes; evaluación con usuarios pendiente |
| Disponibilidad | Indisponibilidad de componente o modelo | **No acreditada:** faltan pruebas de entorno y recuperación |
| Rendimiento y precisión del TCN | MAPE y comportamiento de respaldo | **No acreditados por esta integración:** revisar entregables del equipo ML |

**Resultados locales informados antes de este cierre documental:** 61 pruebas de backend y 9 de frontend aprobadas; Ruff, ESLint y compilación exitosos. Deben volver a verificarse en `develop` tras integrar las ramas. La advertencia de deprecación `anyio` no bloqueó las pruebas.

## 4. Hallazgos / riesgos que impiden aprobar H04 como finalizado

| ID | Hallazgo | Acción necesaria | Responsable sugerido | Estado |
|---|---|---|---|---|
| H04-01 | PR dependientes #39, #40, #41, #42, #43 y #44 aún requieren coordinación de integración | Aprobar/reordenar PR evitando cambios duplicados; validar CI y tests en `develop` | PM + revisores + autores | Abierto |
| H04-02 | HU-04 no demuestra aislamiento en compras, inventario y lotes | Incorporar validaciones a esos módulos cuando estén disponibles; ampliar pruebas de autorización | Responsables de módulos + arquitecta | Abierto |
| H04-03 | No se ha acreditado despliegue real conforme al C4 | Comprobar URLs, Cloud Run, Firebase, Neon, secretos, HTTPS, CORS y migraciones | Responsable de despliegue + arquitecta | Abierto |
| H04-04 | El Charter histórico menciona AWS EC2/Render/Vercel mientras el repositorio describe GCP/Firebase/Neon | Registrar decisión y solicitar aprobación de cambio documental/línea base, sin modificar presupuesto unilateralmente | PM + arquitecta | Abierto |
| H04-05 | Falta revisión y aprobación externa de H04 | Obtener observaciones de Christian y Víctor, subsanar y registrar aprobación de Adrián conforme al proceso del equipo | Revisores + PM | Abierto |
| H04-06 | El JWT de 8 horas se elimina del cliente al cerrar sesión, pero no se revoca del servidor | Documentar el límite y definir controles requeridos para el ambiente público (CSP, rate limit, secretos) | Arquitecta + backend | Abierto |

## 5. Puerta de aceptación y evidencia de cierre

Para declarar H04 cerrado, adjuntar o enlazar:

1. Diagramas C4 revisados, coherentes con código y entorno real.
2. Contrato API y matriz de trazabilidad validados con las historias y su EDT.
3. CI aprobado y pruebas cruzadas por otro integrante; resultado en la rama integrada `develop`.
4. Evidencia de permisos y aislamiento para **todos los módulos implementados**.
5. Evidencia de desplegado real y prueba E2E sobre infraestructura objetivo, o reconocimiento explícito de la excepción aprobada.
6. Registro de observaciones resueltas, revisores, fecha y aprobación PM.

**Dictamen provisional:** la arquitectura de identidad/proveedores cuenta con implementación y evidencia local, pero **H04 no está formalmente aprobado**. No convertir esta evaluación provisional en cierre sin validaciones y firmas.
