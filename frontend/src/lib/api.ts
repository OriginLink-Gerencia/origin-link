import { API_URL } from '../appConfig';
import type { LoginIn, RegistroTostadorIn, TokenOut, Usuario } from './authTypes';

/** El backend determina los c?digos HTTP; se preservan sus mensajes de negocio. */
export class ApiError extends Error {
  readonly status: number; constructor(status: number, message: string) { super(message); this.name = 'ApiError'; this.status = status; }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
    });
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor. Int?ntalo nuevamente.');
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail = body && typeof body === 'object' && 'detail' in body ? body.detail : null;
    const message = typeof detail === 'string' ? detail :
      response.status === 422 ? 'Revisa los datos ingresados.' : 'Ocurri? un error inesperado.';
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const registrarTostador = (datos: RegistroTostadorIn) =>
  api<TokenOut>('/api/v1/auth/registro', { method: 'POST', body: JSON.stringify(datos) });
export const iniciarSesion = (datos: LoginIn) =>
  api<TokenOut>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(datos) });
export const obtenerPerfil = (token: string) =>
  api<Usuario>('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } });

export interface HealthResponse { status: string; app: string; environment: string }
export const getHealth = () => api<HealthResponse>('/health');
