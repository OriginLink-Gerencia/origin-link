# ADR-0001: Un solo repositorio (monorepo) para frontend, backend y modelo

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Responsable:** Adrian Donayre (PM/PO)

## Contexto

El equipo es de 5 personas, todas desarrollan y el MVP debe estar listo en 10 días. Cada historia de
usuario suele tocar la API y la pantalla que la usa.

## Decisión

Un repositorio `origin-link` con las carpetas `frontend/`, `backend/`, `ml/` y `docs/`, y workflows de
GitHub Actions filtrados por carpeta.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Un repo para frontend y otro para backend | Una historia queda repartida en dos PRs; más coordinación y peor trazabilidad |

## Consecuencias

- Un PR por historia de usuario (trazabilidad HU → código → prueba).
- La documentación vive junto al código.
- Los workflows deben filtrar por carpeta para no ejecutar todo en cada cambio.
