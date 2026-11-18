// URL base de la API. En local: http://localhost:8000. En el pipeline se define VITE_API_URL
// con la URL del servicio de Cloud Run.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
