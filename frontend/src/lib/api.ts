import { API_URL } from "../appConfig";

/** Cliente HTTP mínimo para la API de Origin Link. */
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new Error(`Error ${response.status} en ${path}`);
  }
  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  app: string;
  environment: string;
}

export const getHealth = () => api<HealthResponse>("/health");
