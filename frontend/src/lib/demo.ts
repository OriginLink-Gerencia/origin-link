import { locale, languageTags } from "./i18n";

/** Fecha de hoy en la zona horaria del navegador (AAAA-MM-DD). */
function today() {
  const d = new Date();
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, "0"), String(d.getDate()).padStart(2, "0")].join("-");
}
export const TODAY = today();
export type Role = "tostadora" | "cooperativa";
export type Supplier = {
  id: number;
  name: string;
  region: string;
  linked: boolean;
  invited: boolean;
  email?: string;
  contact?: string;
  phone?: string;
  token?: string;
  expires?: number;
};
export type Lot = {
  id: number;
  supplier: number;
  code: string;
  variety: string;
  process: string;
  farm: string;
  altitude: number;
  harvest: number;
  owner?: number;
  region?: string;
  updated?: string;
  documents?: { id: string; name: string }[];
  price: number;
  available: number;
  minimum: number;
  days: number;
  notes: string;
};
export type Receipt = { date: string; kg: number; note: string };
export type Order = {
  id: number;
  lot: number;
  kg: number;
  price: number;
  date: string;
  due: string;
  receipts: Receipt[];
  closed?: boolean;
  roaster?: string;
  roasterId?: number;
};
export type Movement = {
  id: number;
  lot: number;
  kind: "Entrada" | "Consumo" | "Merma" | "Ajuste";
  kg: number;
  date: string;
  note: string;
  order?: number;
};
export type Week = { date: string; kg: number };
export type Data = {
  organization?: number;
  nextOrderId?: number;
  nextLotId?: number;
  suppliers: Supplier[];
  lots: Lot[];
  orders: Order[];
  moves: Movement[];
  history: Week[];
};
export const round = (n: number) => Math.round(n * 100) / 100;
export const kg = (n: number) =>
  n.toLocaleString(languageTags[locale()], { maximumFractionDigits: 2 }) +
  " kg";
export const money = (n: number) => "S/ " + n.toFixed(2);
export const after = (days: number, from = TODAY) =>
  new Date(Date.parse(from + "T12:00:00Z") + days * 86400000)
    .toISOString()
    .slice(0, 10);
export const dateLabel = (date: string) =>
  new Date(date + "T12:00:00Z").toLocaleDateString(languageTags[locale()], {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
export const received = (o: Order) =>
  round(o.receipts.reduce((s, r) => s + r.kg, 0));
export const pending = (o: Order) =>
  o.closed ? 0 : Math.max(0, round(o.kg - received(o)));
export const balance = (d: Data, lot?: number) =>
  round(
    d.moves
      .filter((m) => !lot || m.lot === lot)
      .reduce(
        (s, m) => s + (["Consumo", "Merma"].includes(m.kind) ? -m.kg : m.kg),
        0,
      ),
  );
export const ownLots = (d: Data, supplier: number) =>
  d.lots.filter((l) => !l.owner && l.supplier === supplier);
export const visibleLots = (d: Data) =>
  d.lots.filter(
    (l) =>
      !!l.owner || d.suppliers.some((s) => s.id === l.supplier && s.linked),
  );
export function referenceLot(d: Data) {
  const latest = [...d.orders].sort(
    (a, b) => b.date.localeCompare(a.date) || b.id - a.id,
  )[0];
  return d.lots.find((l) => l.id === latest?.lot);
}
