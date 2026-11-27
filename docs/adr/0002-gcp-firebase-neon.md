# ADR-0002: Cloud Run, Firebase Hosting y Neon en lugar de AWS EC2

- **Estado:** Aceptada
- **Fecha:** 2026-11-18
- **Responsable:** Luciana Choquehuanca (Arquitecta)

## Contexto

El Project Charter (3.9) consideraba AWS EC2 como infraestructura. El equipo no dispone de créditos en
Azure, no pudo crear cuenta en Oracle Cloud y necesita un ambiente de validación sin costo y con
despliegue automático.

## Decisión

- Backend y modelo TCN: **Google Cloud Run** (contenedor Docker).
- Frontend: **Firebase Hosting**.
- Base de datos: **Neon** (PostgreSQL gestionado, plan gratuito).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| AWS EC2 (plan original) | Requiere administrar el servidor (SO, parches, proceso, HTTPS) |
| Azure App Service | Créditos agotados |
| Oracle Cloud | No fue posible crear la cuenta |
| Cloud SQL | Tiene costo por hora aunque no se use; Neon escala a cero |

## Consecuencias

- Cambio respecto a la línea base: registrar en el **registro de cambios** (EDT 1.1.4.2).
- Arranque en frío de Cloud Run tras inactividad; para demos y validaciones usar `--min-instances=1`.
- La imagen usa PyTorch solo CPU para reducir tamaño y tiempo de arranque.
