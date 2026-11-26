import { API_URL } from "../appConfig";

/** Cliente HTTP de la API de Origin Link (prefijo /api/v1). El token de sesión se guarda en el navegador. */
const TOKEN = "ol.token";
export const token = {
  get: () => localStorage.getItem(TOKEN),
  set: (value: string) => localStorage.setItem(TOKEN, value),
  clear: () => localStorage.removeItem(TOKEN),
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type Detail = string | { loc?: (string | number)[]; msg?: string }[] | undefined;
const fields: Record<string, string> = {
  cantidad_kg: "la cantidad",
  precio_kg: "el precio",
  fecha_entrega_acordada: "la fecha de entrega",
  cantidad_recibida_kg: "el peso recibido",
  email: "el correo",
  password: "la contraseña",
};

/** Convierte el `detail` de FastAPI (texto o lista de errores de validación) en un mensaje para la persona. */
export function messageFrom(detail: Detail, status: number): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    const field = String(first.loc?.[first.loc.length - 1] ?? "");
    const prefix = fields[field] ? "Revisa " + fields[field] + ": " : "Revisa los datos: ";
    return prefix + (first.msg ?? "valor no válido").replace(/^Value error, /, "");
  }
  if (status === 401) return "Tu sesión venció. Vuelve a iniciar sesión.";
  if (status === 403) return "No tienes permiso para esta acción.";
  if (status === 413) return "El archivo es demasiado grande.";
  return "No se pudo completar la acción (error " + status + ").";
}

type Options = { method?: string; body?: unknown; form?: FormData; auth?: boolean };

export async function request<T>(path: string, { method = "GET", body, form, auth = true }: Options = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const saved = token.get();
  if (auth && saved) headers.Authorization = "Bearer " + saved;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      method,
      headers,
      body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.", 0);
  }
  if (!response.ok) {
    let detail: Detail;
    try {
      detail = ((await response.json()) as { detail?: Detail }).detail;
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    if (response.status === 401 && auth && saved && !path.startsWith("/auth/")) token.clear();
    throw new ApiError(messageFrom(detail, response.status), response.status);
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}
