# Guía de configuración del despliegue (una sola vez)

Responsable sugerida: Luciana Choquehuanca. Tiempo estimado: 45–60 min.
Al terminar, cada merge a `main` despliega solo el frontend y/o el backend.

## 1. Neon (base de datos)

1. Crear cuenta en <https://neon.com> y un proyecto `originlink` (PostgreSQL 16, región **AWS us-east-1**).
2. Copiar el *connection string* (`postgresql://...neon.tech/neondb?sslmode=require`).

## 2. Google Cloud

En <https://console.cloud.google.com>, crear el proyecto (ej. `originlink-2026`). Luego, en **Cloud Shell**:

```bash
PROJECT_ID=originlink-2026          # cambiar por su ID
REGION=us-east1
REPO=OriginLink-Gerencia/origin-link
gcloud config set project $PROJECT_ID
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com iamcredentials.googleapis.com firebasehosting.googleapis.com

# Repositorio de imágenes Docker
gcloud artifacts repositories create originlink --repository-format=docker --location=$REGION

# Secreto con la URL de Neon (lo lee Cloud Run)
printf '%s' 'PEGAR_CONNECTION_STRING_DE_NEON' | gcloud secrets create originlink-database-url --data-file=-
gcloud secrets add-iam-policy-binding originlink-database-url \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role=roles/secretmanager.secretAccessor

# Cuenta de servicio que usará GitHub Actions
gcloud iam service-accounts create github-deployer --display-name="GitHub Actions"
SA=github-deployer@$PROJECT_ID.iam.gserviceaccount.com
for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA" --role=$ROLE
done

# Workload Identity Federation: GitHub se autentica sin llaves JSON, solo desde este repo
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'"
gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$REPO"

# Valor para el secreto GCP_WIF_PROVIDER:
echo "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github-provider"
```

## 3. Firebase Hosting

1. En <https://console.firebase.google.com> → *Agregar proyecto* → elegir el **mismo** proyecto de GCP.
2. Activar *Hosting*. La URL será `https://<PROJECT_ID>.web.app`.
3. *Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada* (JSON).
   Pegar **todo** el contenido en el secreto `FIREBASE_SERVICE_ACCOUNT` y **borrar el archivo** del disco.

## 4. GitHub (Settings del repo)

**Settings → Environments → New environment →** `validacion`. Dentro del environment:

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `GCP_WIF_PROVIDER` | salida del último `echo` del paso 2 |
| Secret | `GCP_SERVICE_ACCOUNT` | `github-deployer@<PROJECT_ID>.iam.gserviceaccount.com` |
| Secret | `DATABASE_URL` | connection string de Neon (para las migraciones) |
| Secret | `FIREBASE_SERVICE_ACCOUNT` | JSON de la cuenta de servicio de Firebase |
| Variable | `GCP_PROJECT_ID` | `<PROJECT_ID>` |
| Variable | `GCP_REGION` | `us-east1` |
| Variable | `FRONTEND_URL` | `https://<PROJECT_ID>.web.app` |
| Variable | `API_URL` | URL de Cloud Run (se conoce tras el primer despliegue del backend) |

## 5. Primer despliegue

1. *Actions → Deploy backend (Cloud Run) → Run workflow*. Copiar la URL del servicio y guardarla en `API_URL`.
2. *Actions → Deploy frontend (Firebase Hosting) → Run workflow*.
3. Abrir `https://<PROJECT_ID>.web.app`: el panel debe mostrar **Estado de la API: ok (validacion)**.

## Para la demo y las sesiones de validación

Evitar el arranque en frío durante la presentación (consume crédito solo mientras está activo):

```bash
gcloud run services update originlink-api --region=us-east1 --min-instances=1   # antes
gcloud run services update originlink-api --region=us-east1 --min-instances=0   # después
```
