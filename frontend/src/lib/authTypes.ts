/** Tipos del contrato EP-01; no duplican la lógica del servidor. */
export type TipoOrganizacion = 'TOSTADOR' | 'PROVEEDOR';

export interface Organizacion {
  id: number;
  tipo: TipoOrganizacion;
  nombre: string;
  ruc: string | null;
  region: string | null;
}

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  organizacion: Organizacion;
}

export interface TokenOut {
  access_token: string;
  token_type: 'bearer';
  usuario: Usuario;
}

export interface RegistroTostadorIn {
  empresa: string;
  ruc: string | null;
  nombre: string;
  email: string;
  password: string;
}

export interface LoginIn { email: string; password: string }

export interface RegistroPorInvitacionIn extends RegistroTostadorIn {
  token: string;
  region: string | null;
}

export interface InvitacionInfo {
  tostador: string;
  proveedor: string;
  vigente: boolean;
  expira_en: string;
}

export interface VinculoAceptado {
  tostador_id: number;
  tostador: string;
  vinculado_desde: string;
}
