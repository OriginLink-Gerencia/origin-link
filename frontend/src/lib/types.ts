// Tipos del contrato de la API (docs/api/contrato-api.md).
// Deben coincidir con backend/app/schemas/. Si cambia el contrato, actualizar ambos en el mismo PR.

export type ISODate = string; // "2026-11-19"
export type ISODateTime = string; // "2026-11-19T10:00:00-05:00"

// ---------- EP-01 Identidad y acceso ----------
export type TipoOrganizacion = "TOSTADOR" | "PROVEEDOR";

export interface RegistroTostadorIn {
  empresa: string;
  ruc?: string | null;
  nombre: string;
  email: string;
  password: string;
}

export interface RegistroPorInvitacionIn extends RegistroTostadorIn {
  token: string;
  region?: string | null;
}

export interface LoginIn {
  email: string;
  password: string;
}

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
  token_type: "bearer";
  usuario: Usuario;
}

// ---------- EP-02 Proveedores y relaciones ----------
export type EstadoVinculo = "SIN_VINCULAR" | "INVITADO" | "VINCULADO";

export interface ProveedorIn {
  nombre: string;
  region?: string | null;
  contacto_nombre?: string | null;
  contacto_telefono?: string | null;
  contacto_email?: string | null;
}

export interface Proveedor extends Required<ProveedorIn> {
  id: number;
  estado_vinculo: EstadoVinculo;
  organizacion_proveedora_id: number | null;
  creado_en: ISODateTime;
}

export interface Invitacion {
  token: string;
  url: string;
  expira_en: ISODateTime;
}

export interface InvitacionInfo {
  tostador: string;
  proveedor: string;
  vigente: boolean;
  expira_en: ISODateTime;
}

export interface Vinculo {
  tostador_id: number;
  tostador: string;
  vinculado_desde: ISODateTime;
}

// ---------- EP-03 Lotes ----------
export type ProcesoCafe = "LAVADO" | "NATURAL" | "HONEY" | "ANAEROBICO" | "OTRO";

export interface LoteIn {
  proveedor_id?: number | null; // solo HU-11
  codigo: string;
  region: string;
  finca?: string | null;
  variedad: string;
  proceso: ProcesoCafe;
  cosecha: string;
  altitud_msnm?: number | null;
  caracteristicas?: string | null;
  cantidad_disponible_kg: number;
  precio_kg: number;
  cantidad_minima_kg?: number;
  plazo_entrega_dias?: number;
}

export interface DisponibilidadUpdate {
  cantidad_disponible_kg?: number;
  precio_kg?: number;
  cantidad_minima_kg?: number;
  plazo_entrega_dias?: number;
  publicado?: boolean;
}

export interface Lote {
  id: number;
  proveedor_nombre: string;
  registrado_por_tostador: boolean;
  codigo: string;
  region: string;
  finca: string | null;
  variedad: string;
  proceso: ProcesoCafe;
  cosecha: string;
  altitud_msnm: number | null;
  caracteristicas: string | null;
  cantidad_disponible_kg: number;
  precio_kg: number;
  cantidad_minima_kg: number;
  plazo_entrega_dias: number;
  agotado: boolean;
  actualizado_en: ISODateTime;
}

// ---------- EP-04 Compras y recepciones ----------
export type EstadoCompra = "PENDIENTE" | "RECIBIDA" | "ANULADA";

export interface CompraIn {
  lote_id: number;
  cantidad_kg: number;
  precio_kg: number;
  fecha_compra: ISODate;
  fecha_entrega_acordada: ISODate;
  observaciones?: string | null;
}

export interface RecepcionIn {
  fecha_recepcion: ISODate;
  cantidad_recibida_kg: number;
  observaciones?: string | null;
}

export interface Recepcion {
  id: number;
  fecha_recepcion: ISODate;
  cantidad_recibida_kg: number;
  diferencia_kg: number; // negativo = faltante
  observaciones: string | null;
}

export interface Compra {
  id: number;
  lote_id: number;
  lote_codigo: string;
  proveedor_id: number;
  proveedor_nombre: string;
  cantidad_kg: number;
  precio_kg: number;
  total: number;
  fecha_compra: ISODate;
  fecha_entrega_acordada: ISODate;
  estado: EstadoCompra;
  observaciones: string | null;
  recepcion: Recepcion | null;
  advertencia: string | null;
}

// ---------- EP-05 Inventario ----------
export type TipoMovimiento = "ENTRADA" | "CONSUMO" | "MERMA" | "AJUSTE";

export interface MovimientoIn {
  lote_id: number;
  tipo: Exclude<TipoMovimiento, "ENTRADA">;
  cantidad_kg: number; // con signo solo en AJUSTE
  fecha: ISODate;
  motivo?: string | null; // obligatorio en AJUSTE
}

export interface Movimiento {
  id: number;
  lote_id: number;
  tipo: TipoMovimiento;
  cantidad_kg: number;
  fecha: ISODate;
  motivo: string | null;
  creado_en: ISODateTime;
}

export interface Existencias {
  total_kg: number;
  lotes: { lote_id: number; lote_codigo: string; proveedor_nombre: string; existencias_kg: number }[];
}

export interface Importacion {
  semanas_importadas: number;
  desde: ISODate | null;
  hasta: ISODate | null;
  errores: { fila: number; error: string }[];
}

// ---------- EP-06 / EP-07 Pronóstico y recomendaciones (Sprint B, preliminar) ----------
export type MetodoPronostico = "TCN" | "PROMEDIO_MOVIL";

export interface PuntoSerie {
  semana: ISODate;
  kg: number;
}

export interface Pronostico {
  metodo: MetodoPronostico;
  motivo_metodo: string | null;
  historial: PuntoSerie[];
  pronostico: PuntoSerie[];
  mape_referencia: number | null;
}

export interface Recomendacion {
  fecha_limite_compra: ISODate;
  cantidad_sugerida_kg: number;
  semanas_cobertura_actual: number;
  factores: {
    existencias_kg: number;
    consumo_semanal_pronosticado_kg: PuntoSerie[];
    plazo_entrega_dias: number;
    semanas_cobertura: number;
    cantidad_minima_kg: number;
    metodo_pronostico: MetodoPronostico;
  };
  explicacion: string;
}

export interface Alerta {
  tipo: "STOCK_BAJO" | "COMPRA_PROXIMA";
  mensaje: string;
  semanas_cobertura_restantes: number;
  fecha_limite_compra: ISODate;
}
