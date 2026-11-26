import { locale, languageTags } from "./i18n";
import { projection } from "./projection";
import database from "../../db.json";

export const TODAY = "2026-11-25";
export const KEY = "originlink.piloto.v1";
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
export const nextId = (items: { id: number }[]) =>
  Math.max(0, ...items.map((x) => x.id)) + 1;
const requireRule = (ok: boolean, message: string) => {
  if (!ok) throw new Error(message);
};
const positive = (n: number) => Number.isFinite(n) && n > 0 && round(n) === n;
export function seed(): Data {
  // Clone the fixture so each interview starts with independent records.
  const moves = database.moves.map((movement): Movement => {
    const kind = movement.kind;
    if (
      kind !== "Entrada" &&
      kind !== "Consumo" &&
      kind !== "Merma" &&
      kind !== "Ajuste"
    ) {
      throw new Error("Tipo de movimiento desconocido en db.json: " + kind);
    }
    return { ...movement, kind };
  });
  return JSON.parse(
    JSON.stringify({
      suppliers: database.suppliers,
      lots: database.lots,
      orders: database.orders,
      history: database.history,
      moves,
    } satisfies Data),
  );
}

export function loadDemo(): Data {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const d = JSON.parse(raw);
      if (
        ["suppliers", "lots", "orders", "moves", "history"].every((k) =>
          Array.isArray(d[k]),
        )
      )
        return d;
    }
  } catch {
    /* recover from invalid browser data */
  }
  return seed();
}
export function referenceLot(d: Data) {
  const latest = [...d.orders].sort(
    (a, b) => b.date.localeCompare(a.date) || b.id - a.id,
  )[0];
  return d.lots.find((l) => l.id === latest?.lot);
}
export function forecast(
  d: Data,
  days = referenceLot(d)?.days ?? 7,
  minimum = referenceLot(d)?.minimum ?? 0,
) {
  const first = after(8 - (new Date(TODAY + "T12:00:00Z").getUTCDay() || 7));
  const currentMonday = after(-7, first);
  const weeks = new Map(d.history.map((w) => [w.date, w.kg]));
  const importedWeeks = new Set(weeks.keys());
  for (const m of d.moves.filter((m) => m.kind === "Consumo")) {
    const weekday = new Date(m.date + "T12:00:00Z").getUTCDay();
    const monday = after(-((weekday + 6) % 7), m.date);
    if (monday < currentMonday && !importedWeeks.has(monday))
      weeks.set(monday, round((weeks.get(monday) ?? 0) + m.kg));
  }
  const history = Array.from(weeks, ([date, amount]) => ({
    date,
    kg: amount,
  }))
    .filter((w) => w.date < currentMonday)
    .sort((a, b) => a.date.localeCompare(b.date));
  const prediction = projection(history, d.organization, first);
  const demand = round(prediction.values.reduce((sum, n) => sum + n, 0));
  const mean = demand / 4;
  function consumption(days: number) {
    let total = 0;
    prediction.values.forEach((amount) => {
      const part = Math.min(7, Math.max(0, days));
      total += (amount * part) / 7;
      days -= part;
    });
    return total + (Math.max(0, days) * mean) / 7;
  }
  const stock = balance(d);
  const incoming = d.orders
    .filter((o) => o.due <= after(28))
    .reduce((s, o) => s + pending(o), 0);
  let daysStock = 0,
    remaining = stock;
  if (mean > 0) {
    for (const amount of prediction.values) {
      if (amount && remaining < amount) {
        daysStock += Math.floor((remaining * 7) / amount);
        remaining = 0;
        break;
      }
      daysStock += 7;
      remaining -= amount;
    }
    if (remaining > 0) daysStock += Math.floor((remaining * 7) / mean);
  }
  const required = round(Math.max(0, consumption(days + 14) - stock));
  return {
    history,
    mean,
    demand,
    prediction,
    first,
    stock,
    incoming,
    gap: Math.max(0, round(mean * 4 - stock - incoming)),
    need: minimum ? round(Math.ceil(required / minimum) * minimum) : required,
    days,
    minimum,
    low: mean > 0 && stock < consumption(days),
    date: after(Math.max(0, daysStock - days)),
    daysStock,
  };
}
export function buy(
  d: Data,
  id: number,
  amount: number,
  price: number,
  due: string,
): Data {
  const l = visibleLots(d).find((l) => l.id === id);
  requireRule(
    !!l && positive(amount) && amount >= l.minimum && amount <= l.available,
    l && amount > l.available
      ? "La cantidad supera lo disponible en este lote."
      : "Revisa el mínimo y la disponibilidad del lote.",
  );
  requireRule(
    positive(price) && !!due && due >= TODAY,
    "Revisa el precio y la fecha acordada.",
  );
  return {
    ...d,
    lots: d.lots.map((l) =>
      l.id === id ? { ...l, available: round(l.available - amount) } : l,
    ),
    orders: [
      {
        id: d.nextOrderId ?? nextId(d.orders),
        lot: id,
        kg: amount,
        price,
        date: TODAY,
        due,
        receipts: [],
      },
      ...d.orders,
    ],
  };
}
export function receive(
  d: Data,
  id: number,
  amount: number,
  note: string,
  final = false,
): Data {
  const o = d.orders.find((o) => o.id === id);
  requireRule(
    !!o &&
      pending(o) > 0 &&
      positive(amount) &&
      (final || amount <= pending(o)),
    "El peso debe ser positivo y no superar el saldo pendiente.",
  );
  if (!o) throw new Error("Compra no disponible.");
  requireRule(
    !final || amount === pending(o) || !!note.trim(),
    "Indica el motivo de la diferencia de peso.",
  );
  const receipt = { date: TODAY, kg: amount, note: note.trim() };
  return {
    ...d,
    orders: d.orders.map((x) =>
      x.id === id
        ? {
            ...x,
            closed: final || amount === pending(o),
            receipts: [...x.receipts, receipt],
          }
        : x,
    ),
    moves: [
      ...d.moves,
      {
        id: nextId(d.moves),
        lot: o.lot,
        kind: "Entrada",
        order: id,
        ...receipt,
      },
    ],
  };
}
export function move(
  d: Data,
  id: number,
  kind: Exclude<Movement["kind"], "Entrada">,
  amount: number,
  note: string,
): Data {
  requireRule(
    visibleLots(d).some((l) => l.id === id) &&
      positive(Math.abs(amount)) &&
      (kind === "Ajuste" || amount > 0),
    "Ingresa una cantidad válida.",
  );
  requireRule(
    kind !== "Ajuste" || !!note.trim(),
    "Indica el motivo del ajuste.",
  );
  requireRule(
    balance(d, id) + (kind === "Ajuste" ? amount : -amount) >= 0,
    "El movimiento dejaría el lote con saldo negativo.",
  );
  return {
    ...d,
    moves: [
      ...d.moves,
      {
        id: nextId(d.moves),
        date: TODAY,
        lot: id,
        kind,
        kg: amount,
        note: note.trim(),
      },
    ],
  };
}
export function setLot(d: Data, supplier: number, lot: Lot): Data {
  requireRule(
    d.suppliers.some(
      (s) => s.id === supplier && (lot.owner ? !s.linked : s.linked),
    ) && lot.supplier === supplier,
    "Se necesita un vínculo activo.",
  );
  requireRule(
    !lot.id || ownLots(d, supplier).some((l) => l.id === lot.id),
    "Este lote pertenece a otro proveedor.",
  );
  requireRule(
    !d.lots.some(
      (l) => l.id !== lot.id && l.code.toLowerCase() === lot.code.toLowerCase(),
    ),
    "Ya existe un lote con ese código.",
  );
  requireRule(
    lot.code.trim() !== "" &&
      lot.variety.trim() !== "" &&
      lot.farm.trim() !== "" &&
      (lot.id ? lot.available >= 0 : lot.available > 0) &&
      Number.isFinite(lot.available) &&
      Number.isFinite(lot.altitude) &&
      lot.altitude > 0 &&
      positive(lot.minimum) &&
      positive(lot.price) &&
      Number.isInteger(lot.days) &&
      lot.days >= 1,
    "Revisa los datos del lote.",
  );
  return {
    ...d,
    lots: lot.id
      ? d.lots.map((l) => (l.id === lot.id ? { ...lot, updated: TODAY } : l))
      : [
          ...d.lots,
          { ...lot, updated: TODAY, id: d.nextLotId ?? nextId(d.lots) },
        ],
  };
}
