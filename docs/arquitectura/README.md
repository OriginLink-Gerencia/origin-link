# Arquitectura de Origin Link

Responsable: Luciana Choquehuanca (Arquitecta de Software). Revisión técnica: Christian Inga y Victor Cruz.
Modelo C4 (contexto y contenedores) y vista de despliegue. Las decisiones se registran como ADRs en [`../adr`](../adr).

> Borrador inicial generado con el esqueleto del repo: revisar, completar y aprobar (hito H04).

## 1. Contexto (C4 nivel 1)

```mermaid
flowchart LR
    tostador["👤 Tostador de café de especialidad<br/><i>Planifica compras, registra lotes,<br/>compras, recepciones y consumos</i>"]
    coop["👤 Empresa productora o cooperativa<br/><i>Publica lotes, disponibilidad y<br/>condiciones de abastecimiento</i>"]
    ol["<b>Origin Link</b><br/>Aplicativo web colaborativo de<br/>abastecimiento con pronóstico TCN"]

    tostador -- "Invita proveedores, consulta pronóstico<br/>y recomendaciones de compra" --> ol
    coop -- "Publica lotes a tostadores vinculados<br/>(solo por invitación)" --> ol
```

Fuera del alcance (exclusiones del Project Charter): pagos, facturación, logística, marketplace público,
datos climáticos externos y recomendación de proveedor.

## 2. Contenedores (C4 nivel 2)

```mermaid
flowchart TB
    usuario["👤 Tostador / Cooperativa<br/>(navegador web)"]

    subgraph ol["Origin Link"]
        spa["<b>Aplicación web (SPA)</b><br/>React 18 + TypeScript + Tailwind<br/><i>Pantallas de proveedores, lotes,<br/>compras, inventario y pronóstico</i>"]
        api["<b>API REST</b><br/>Python 3.11 + FastAPI<br/><i>Lógica de negocio, cálculo de existencias,<br/>motor de recomendaciones</i>"]
        modelo["<b>Servicio de pronóstico</b><br/>PyTorch (TCN) dentro de la API<br/><i>Respaldo: promedio móvil 4 semanas</i>"]
        db[("<b>Base de datos</b><br/>PostgreSQL 16<br/><i>Usuarios, vínculos, lotes, compras,<br/>movimientos e historial de consumo</i>")]
    end

    usuario -- "HTTPS" --> spa
    spa -- "JSON/HTTPS" --> api
    api -- "Invoca" --> modelo
    api -- "SQL (SQLAlchemy)" --> db
    modelo -- "Lee historial de consumo" --> db
```

## 3. Despliegue

```mermaid
flowchart LR
    dev["👩‍💻 Equipo<br/>(feature/HU-XX)"] -- "PR" --> gh["GitHub<br/>develop → main"]
    gh -- "CI: lint + pruebas" --> ci["GitHub Actions"]
    ci -- "merge a main" --> fb["Firebase Hosting<br/>(frontend estático)"]
    ci -- "imagen Docker" --> ar["Artifact Registry"] --> cr["Cloud Run<br/>originlink-api<br/>(FastAPI + TCN)"]
    ci -- "alembic upgrade head" --> neon[("Neon<br/>PostgreSQL")]
    cr -- "DATABASE_URL<br/>(Secret Manager)" --> neon
    usuario["👤 Usuario"] -- "HTTPS" --> fb
    fb -. "llamadas a la API" .-> cr
```

| Elemento | Servicio | Motivo |
|---|---|---|
| Frontend | Firebase Hosting | CDN, HTTPS y despliegue desde GitHub Actions sin costo |
| Backend + modelo | Cloud Run | Contenedor sin administrar servidores, escala a cero, capa gratuita mensual |
| Base de datos | Neon | PostgreSQL gestionado con plan gratuito permanente |
| Imágenes | Artifact Registry | Repositorio de imágenes Docker en GCP |
| Secretos | Secret Manager + GitHub Secrets | Sin credenciales en el código |

## 4. Módulos de la API (alineados a la EDT)

Detalle completo en el [contrato de la API](../api/contrato-api.md) y el [modelo de datos](modelo-de-datos.md).

| Módulo | Ruta base | EDT |
|---|---|---|
| Identidad y acceso | `/api/v1/auth` | 1.4.2 |
| Proveedores y relaciones | `/api/v1/proveedores`, `/api/v1/invitaciones`, `/api/v1/vinculos` | 1.4.3 |
| Colaborativo (lotes) | `/api/v1/lotes` | 1.4.4 |
| Compras y recepciones | `/api/v1/compras`, `/api/v1/compras/{id}/recepcion` | 1.4.5 |
| Inventario | `/api/v1/movimientos`, `/api/v1/existencias`, `/api/v1/consumo-historico/importar` | 1.4.6 |
| Pronóstico y recomendación | `/api/v1/pronostico`, `/api/v1/recomendaciones`, `/api/v1/alertas` | 1.5.3–1.5.5 |

## 5. Atributos de calidad (pendiente de completar)

| Atributo | Escenario | Medida |
|---|---|---|
| Usabilidad | Un tostador registra un consumo semanal | ≥ 68/100 en el cuestionario (OE4-I1) |
| Precisión | Pronóstico de 4 semanas | MAPE ≤ 25 % y menor que el promedio móvil |
| Seguridad | Una cooperativa sin invitación intenta ver lotes | Acceso denegado (403) |
| Disponibilidad | Falla el modelo TCN | Se responde con el promedio móvil (respaldo) |
