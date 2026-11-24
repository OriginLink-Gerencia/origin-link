# Origin Link — HU-01/HU-02, entrega de integración

## Qué contiene
El ZIP conserva todo el árbol de `develop` recibido y añade/actualiza los módulos
de registro, login, perfil, formularios React, guardas de rutas, logout, pruebas y ADR.

## BLOQUEO DE DEPENDENCIA — PR #35
Este snapshot de `develop` no contiene `app.models.identidad`, `app.models.enums`,
`app.schemas.auth` ni las migraciones. El backend de este paquete NO arrancará hasta
que se incorporen esos modelos del **PR #35 CORREGIDO Y APROBADO**. No se incluyen
versiones duplicadas de los modelos para evitar conflictos de integración.
No hacer merge directo a `develop` ni sobrescribir el árbol local completo.

## Estrategia de integración segura (PowerShell, desde la raíz de tu clon)
1. Confirma `git status` limpio y `git branch --show-current` -> `feature/HU-01-registro`.
2. Espera merge PR #35 después de atender las observaciones; luego:
   `git fetch origin` y `git merge origin/develop` (resolver conflictos si aparecen).
3. Copia **únicamente archivos añadidos/modificados de HU-01/HU-02** desde el ZIP,
   no reemplaces el repositorio ni `.env` ni otras ramas. Los nombres están en este documento.
4. Crea `backend/.env` desde `backend/.env.example` y configura `DATABASE_URL`
   y `JWT_SECRET_KEY` (no publiques estas credenciales).
5. Migraciones PostgreSQL desde backend: `python -m alembic upgrade head`.
6. Backend: `python -m pytest`; `python -m ruff check app tests`;
   `python -m uvicorn app.main:app --reload`.
7. Frontend: `npm ci`; `npm run typecheck`; `npm test -- --runInBand`;
   `npm run lint`; `npm run build`; `npm run dev`.
8. Probar registro → panel → logout → login → `/auth/me`.
9. Crear PR a `develop` (no `main`), sujeto a revisión del equipo.

## Archivos del cambio
Backend:
- `backend/app/api/routes/auth.py` nuevo
- `backend/app/core/auth_security.py` nuevo
- `backend/app/services/auth_service.py` nuevo
- `backend/app/main.py` editado
- `backend/app/core/config.py` editado
- `backend/.env.example` editado

Frontend:
- `frontend/src/lib/authTypes.ts` nuevo
- `frontend/src/lib/api.ts` editado
- `frontend/src/auth/AuthContext.tsx` nuevo
- `frontend/src/components/ProtectedRoute.tsx` nuevo
- `frontend/src/components/RoleRoute.tsx` nuevo
- `frontend/src/pages/Login.tsx` nuevo
- `frontend/src/pages/Registro.tsx` nuevo
- `frontend/src/pages/Inicio.tsx` editado
- `frontend/src/App.tsx` editado
- `frontend/src/components/Layout.tsx` editado
- `frontend/src/App.test.tsx` editado

Documentación:
- `docs/adr/0004-identidad-seguridad.md` nuevo

## Límites
- Código generado como propuesta: no autoriza cambiar tareas asignadas a otros integrantes.
- Tests de backend requieren migración/modelos del PR #35 y PostgreSQL de pruebas.
- El proyecto original no incluye login previo; se mantiene estilo visual existente.
- HU-03, HU-04 y otros módulos de negocio NO se implementan en este paquete.

## Revisión frente al Project Charter (12/11/2026)
Leer `docs/arquitectura/REVISION_ALINEAMIENTO_HU01_HU02.md` antes de integrar.
Contiene trazabilidad de criterios HU-01/HU-02, riesgos, diferencias de infraestructura,
las pruebas obligatorias y la definición de monolito modular.

**Corrección sobre instrucciones anteriores:** `npm run typecheck` existe, pero la puerta de CI
real ejecuta `npm run lint`, `npm test -- --coverage` y `npm run build`.
