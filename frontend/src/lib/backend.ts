// Respuestas de la API (backend/app/schemas) y su conversión a los tipos que usa la interfaz (lib/demo.ts).
import type { Lot, Movement, Order, Supplier, Week } from "./demo";

export type Process = "LAVADO" | "HONEY" | "NATURAL" | "ANAEROBICO" | "OTRO";
export const processLabels: Record<Process, string> = {
  LAVADO: "Lavado",
  HONEY: "Honey",
  NATURAL: "Natural",
  ANAEROBICO: "Anaeróbico",
  OTRO: "Otro",
};
export const processCodes = Object.fromEntries(Object.entries(processLabels).map(([k, v]) => [v, k])) as Record<string, Process>;

export type SupplierDTO = {
  id: number;
  nombre: string;
  region: string | null;
  contacto_nombre: string | null;
  contacto_telefono: string | null;
  contacto_email: string | null;
  estado_vinculo: "SIN_VINCULAR" | "INVITADO" | "VINCULADO";
  invitacion_vigente: { token: string; expira_en: string } | null;
};
export type LotDTO = {
  id: number;
  proveedor_id: number | null;
  proveedor_nombre: string;
  registrado_por_tostador: boolean;
  codigo: string;
  region: string;
  finca: string | null;
  variedad: string;
  proceso: Process;
  cosecha: string;
  altitud_msnm: number | null;
  caracteristicas: string | null;
  cantidad_disponible_kg: number;
  precio_kg: number;
  cantidad_minima_kg: number;
  plazo_entrega_dias: number;
  actualizado_en: string;
};
export type PurchaseDTO = {
  id: number;
  lote_id: number;
  cantidad_kg: number;
  precio_kg: number;
  fecha_compra: string;
  fecha_entrega_acordada: string;
  estado: "PENDIENTE" | "RECIBIDA" | "ANULADA";
  recepcion: { fecha_recepcion: string; cantidad_recibida_kg: number; observaciones: string | null } | null;
  advertencia: string | null;
};
export type MovementDTO = {
  id: number;
  lote_id: number;
  tipo: "ENTRADA" | "CONSUMO" | "MERMA" | "AJUSTE";
  cantidad_kg: number;
  fecha: string;
  motivo: string | null;
};
export type ReceivedOrderDTO = {
  id: number;
  tostador: string;
  lote_id: number;
  cantidad_kg: number;
  recibido_kg: number;
  fecha_compra: string;
  fecha_entrega_acordada: string;
  estado: "PENDIENTE" | "RECIBIDA" | "ANULADA";
};
export type Point = { semana: string; kg: number };
export type ForecastDTO = {
  metodo: "TCN" | "PROMEDIO_MOVIL";
  motivo_metodo: string | null;
  historial: Point[];
  pronostico: Point[];
  mape_referencia: number | null;
};
export type RecommendationDTO = {
  fecha_limite_compra: string;
  cantidad_sugerida_kg: number;
  semanas_cobertura_actual: number;
  dias_cobertura_actual: number | null;
  factores: {
    existencias_kg: number;
    plazo_entrega_dias: number;
    semanas_cobertura: number;
    cantidad_minima_kg: number;
    metodo_pronostico: "TCN" | "PROMEDIO_MOVIL";
  };
  explicacion: string;
};
export type AlertDTO = {
  tipo: "STOCK_BAJO" | "COMPRA_PROXIMA";
  mensaje: string;
  semanas_cobertura_restantes: number;
  fecha_limite_compra: string;
};

export const toSupplier = (p: SupplierDTO): Supplier => ({
  id: p.id,
  name: p.nombre,
  region: p.region ?? "",
  linked: p.estado_vinculo === "VINCULADO",
  invited: p.estado_vinculo === "INVITADO",
  email: p.contacto_email ?? undefined,
  contact: p.contacto_nombre ?? undefined,
  phone: p.contacto_telefono ?? undefined,
  token: p.invitacion_vigente?.token,
  expires: p.invitacion_vigente ? Date.parse(p.invitacion_vigente.expira_en) : undefined,
});

/** `own` es el id con el que la interfaz agrupa los lotes de una cooperativa (el de su organización). */
export const toLot = (l: LotDTO, own: number): Lot => ({
  id: l.id,
  supplier: l.proveedor_id ?? own,
  owner: l.registrado_por_tostador ? own : undefined,
  code: l.codigo,
  region: l.region,
  farm: l.finca ?? "",
  variety: l.variedad,
  process: processLabels[l.proceso] ?? l.proceso,
  harvest: Number(l.cosecha) || new Date().getFullYear(),
  altitude: l.altitud_msnm ?? 0,
  price: l.precio_kg,
  available: l.cantidad_disponible_kg,
  minimum: l.cantidad_minima_kg,
  days: l.plazo_entrega_dias,
  notes: l.caracteristicas ?? "",
  updated: l.actualizado_en.slice(0, 10),
});

export const toOrder = (c: PurchaseDTO): Order => ({
  id: c.id,
  lot: c.lote_id,
  kg: c.cantidad_kg,
  price: c.precio_kg,
  date: c.fecha_compra,
  due: c.fecha_entrega_acordada,
  receipts: c.recepcion
    ? [{ date: c.recepcion.fecha_recepcion, kg: c.recepcion.cantidad_recibida_kg, note: c.recepcion.observaciones ?? "" }]
    : [],
  closed: c.estado !== "PENDIENTE",
});

export const toReceivedOrder = (p: ReceivedOrderDTO): Order => ({
  id: p.id,
  lot: p.lote_id,
  kg: p.cantidad_kg,
  price: 0,
  date: p.fecha_compra,
  due: p.fecha_entrega_acordada,
  receipts: p.recibido_kg > 0 ? [{ date: p.fecha_entrega_acordada, kg: p.recibido_kg, note: "" }] : [],
  closed: p.estado !== "PENDIENTE",
  roaster: p.tostador,
});

const kinds = { ENTRADA: "Entrada", CONSUMO: "Consumo", MERMA: "Merma", AJUSTE: "Ajuste" } as const;
export const toMovement = (m: MovementDTO): Movement => ({
  id: m.id,
  lot: m.lote_id,
  kind: kinds[m.tipo],
  kg: m.cantidad_kg,
  date: m.fecha,
  note: m.motivo ?? "",
});
export const movementCodes = { Consumo: "CONSUMO", Merma: "MERMA", Ajuste: "AJUSTE" } as const;

export const toWeek = (p: Point): Week => ({ date: p.semana, kg: p.kg });
