# Origin Link

Aplicativo web colaborativo para la planificación del abastecimiento de café verde de pequeños tostadores de
café de especialidad de Lima, con pronóstico de demanda mediante una Red Neuronal Convolucional Temporal (TCN).

Curso 1ASI0727 Gerencia de Proyectos en Computación · UPC · 2026-2 · Equipo 3

## Estructura del monorepo

```
origin-link/
├── frontend/   React 18 + TypeScript + TailwindCSS 3.4 (Vite) · Jest · Firebase Hosting
├── backend/    Python 3.11 + FastAPI · SQLAlchemy + Alembic · PyTest · Cloud Run
├── ml/         Modelo TCN (PyTorch), promedio móvil de referencia y MAPE
├── docs/       Arquitectura (C4), ADRs y guía de despliegue
└── .github/    CI/CD, plantillas de épicas, historias de usuario, defectos y PR
```

| Capa | Servicio | Despliegue |
|---|---|---|
| Frontend | Firebase Hosting | Automático al hacer merge a `main` (`deploy-frontend.yml`) |
| Backend + modelo | Cloud Run | Automático al hacer merge a `main` (`deploy-backend.yml`) |
| Base de datos | Neon (PostgreSQL) | Migraciones con Alembic dentro del pipeline del backend |

## Desarrollo local

Requisitos: Git, Docker Desktop, Python 3.11, Node 22.

```bash
# 1. Base de datos local
docker compose up -d

# 2. Backend  →  http://localhost:8000/docs
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env            # Linux/Mac: cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend  →  http://localhost:5173
cd frontend
npm install
npm run dev
```

Pruebas: `pytest` (backend y ml) · `npm test` (frontend).

## Flujo de trabajo

### Ramas

| Rama | Sale de → entra a | Uso |
|---|---|---|
| `main` | ← solo PR desde `develop` o `hotfix/*` | Lo desplegado en el ambiente de validación |
| `develop` | rama por defecto | Integración diaria |
| `feature/HU-XX-descripcion` | `develop` → `develop` | Una historia de usuario por rama |
| `fix/HU-XX-descripcion` | `develop` → `develop` | Defectos de las pruebas cruzadas |
| `hotfix/descripcion` | `main` → `main` y `develop` | Urgencias en lo desplegado |
| `docs/...`, `chore/...` | `develop` → `develop` | Documentación y configuración |

### Reglas del equipo

1. **Nadie hace push directo a `main` ni a `develop`**: todo entra por Pull Request.
2. Cada PR lo aprueba **otro integrante** (pruebas cruzadas) y debe tener el CI en verde.
3. Ramas cortas: máximo 1–2 días. Antes de abrir el PR: `git pull origin develop`.
4. Merge a `develop` con **Squash and merge**; de `develop` a `main` con **Create a merge commit**.
5. El PR se titula como la historia (`HU-03 Publicar lote`) e incluye `Closes #<issue>`.
6. Commits con prefijo: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`.
7. Tags de versión: `v0.1.0` (avance al docente), `v1.0.0` (entrega final).

### Gestión ágil

- **Épicas e historias de usuario**: issues con las plantillas de `.github/ISSUE_TEMPLATE`.
- **Product Backlog y Sprints**: GitHub Projects de la organización (campo *Iteration* para los sprints).
- **Definition of Done**: checklist en la plantilla de PR.

## Equipo

| Rol | Integrante |
|---|---|
| Project Manager / Product Owner | Adrian Donayre |
| Arquitecta de Software | Luciana Choquehuanca |
| Scrum Master | Rafael Vivanco |
| Developer Frontend y QA | Christian Inga |
| Developer Backend e IA | Victor Cruz |
