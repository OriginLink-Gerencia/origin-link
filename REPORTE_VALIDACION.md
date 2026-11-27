# Estado de verificación de la entrega (24/11/2026)

- **Fuente de código:** ZIP `origin-link-develop(2).zip` adjuntado por el equipo.
- **Fuente de requisitos:** `Project Charter - EQUIPO 3 (14).pdf`, especialmente secciones 3.4, 4.2.1, 12.1.3 y 12.1.4.
- **Contrato y modelos pendientes:** PR #35 `docs/modelo-datos-api`, aún sin fusionar.
- **Comprobado:** sintaxis de Python (`compileall`) de archivos de `backend/app` y `backend/tests` — OK.
- **No ejecutado:** pytest de integración, porque faltan los modelos y migraciones de PR #35.
- **No ejecutado:** lint, Jest y build de React; el entorno no tiene las dependencias instaladas correctamente (`eslint` no se encontró).
- **No acreditado:** CI verde, revisión cruzada, despliegue a GCP, aprobación de PM.
- **Consecuencia:** entrega preparada para integrar y probar; no considerar HU-01/HU-02 Done.

## Cuestiones que requieren revisión por el equipo

- Confirmar el PR #35 corregido antes del merge, en especial unicidad entre origen de lote y recepción/movimiento.
- Resolver la divergencia de infraestructura entre el Charter y el ADR-0002 para conservar consistencia documental.
- Confirmar el rol de Luciana y los desarrolladores: el Charter muestra owner de HU-01/HU-02 en Luciana, pero atribuye frontend a Christian y backend a Victor; revisar cómo se implementarán las pruebas cruzadas sin autoaprobación.
- HU-02, cierre de sesión: se elimina JWT del cliente; el JWT no se revoca antes de vencer, tal como dicta el contrato.
