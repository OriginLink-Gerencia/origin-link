import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { balance, pending } from "./lib/demo";
import { toLot, toMovement, toOrder, toSupplier, type LotDTO, type PurchaseDTO } from "./lib/backend";
import { messageFrom } from "./lib/http";
import { emptyPlan, summary } from "./lib/plan";

const lot: LotDTO = {
  id: 7, proveedor_id: 3, proveedor_nombre: "Coop. Jaén", registrado_por_tostador: false, codigo: "JAEN-2026-07",
  region: "Cajamarca", finca: "El Mirador", variedad: "Caturra", proceso: "LAVADO", cosecha: "2026", altitud_msnm: 1650,
  caracteristicas: null, cantidad_disponible_kg: 300, precio_kg: 28.5, cantidad_minima_kg: 30, plazo_entrega_dias: 10,
  actualizado_en: "2026-11-20T10:00:00Z",
};
const purchase: PurchaseDTO = {
  id: 4, lote_id: 7, cantidad_kg: 40, precio_kg: 28.5, fecha_compra: "2026-11-01", fecha_entrega_acordada: "2026-11-08",
  estado: "PENDIENTE", recepcion: null, advertencia: null,
};

test("convierte un lote de la API a la ficha de la interfaz", () => {
  expect(toLot(lot, 1)).toMatchObject({ id: 7, supplier: 3, owner: undefined, code: "JAEN-2026-07", process: "Lavado", harvest: 2026, farm: "El Mirador", days: 10, minimum: 30, updated: "2026-11-20" });
  expect(toLot({ ...lot, proveedor_id: null, registrado_por_tostador: true }, 1)).toMatchObject({ supplier: 1, owner: 1 });
});

test("una compra pendiente tiene saldo y una recibida o anulada no", () => {
  expect(pending(toOrder(purchase))).toBe(40);
  const recibida = toOrder({ ...purchase, estado: "RECIBIDA", recepcion: { fecha_recepcion: "2026-11-08", cantidad_recibida_kg: 38, observaciones: "Faltaron 2 kg" } });
  expect(recibida.receipts).toEqual([{ date: "2026-11-08", kg: 38, note: "Faltaron 2 kg" }]);
  expect(pending(recibida)).toBe(0);
  expect(pending(toOrder({ ...purchase, estado: "ANULADA" }))).toBe(0);
});

test("el saldo del inventario suma entradas y ajustes, y resta consumos y mermas", () => {
  const moves = [
    { id: 1, lote_id: 7, tipo: "ENTRADA", cantidad_kg: 40, fecha: "2026-11-08", motivo: null },
    { id: 2, lote_id: 7, tipo: "CONSUMO", cantidad_kg: 8, fecha: "2026-11-09", motivo: null },
    { id: 3, lote_id: 7, tipo: "AJUSTE", cantidad_kg: -2, fecha: "2026-11-10", motivo: "Conteo" },
  ] as const;
  const data = { suppliers: [], lots: [], orders: [], history: [], moves: moves.map(toMovement) };
  expect(balance(data)).toBe(30);
});

test("un proveedor invitado trae su enlace y un vinculado ya no", () => {
  const base = { id: 2, nombre: "Finca", region: null, contacto_nombre: null, contacto_telefono: null, contacto_email: null };
  const invitado = toSupplier({ ...base, estado_vinculo: "INVITADO", invitacion_vigente: { token: "abc", expira_en: "2099-01-01T00:00:00Z" } });
  expect(invitado).toMatchObject({ invited: true, linked: false, token: "abc" });
  expect(toSupplier({ ...base, estado_vinculo: "VINCULADO", invitacion_vigente: null })).toMatchObject({ linked: true, invited: false, token: undefined });
});

test("el resumen toma la recomendación del servidor y descuenta lo que viene en camino", () => {
  const plan = {
    ...emptyPlan,
    forecast: { metodo: "PROMEDIO_MOVIL" as const, motivo_metodo: "El modelo TCN no está disponible", mape_referencia: 12.5,
      historial: [{ semana: "2026-11-16", kg: 7 }], pronostico: [0, 1, 2, 3].map((i) => ({ semana: "2026-11-2" + (3 + i), kg: 7 })) },
    recommendation: { fecha_limite_compra: "2026-11-30", cantidad_sugerida_kg: 30, semanas_cobertura_actual: 2.1, dias_cobertura_actual: 15,
      factores: { existencias_kg: 15, plazo_entrega_dias: 10, semanas_cobertura: 2, cantidad_minima_kg: 30, metodo_pronostico: "PROMEDIO_MOVIL" as const }, explicacion: "" },
    alerts: [{ tipo: "STOCK_BAJO" as const, mensaje: "", semanas_cobertura_restantes: 2.1, fecha_limite_compra: "2026-11-30" }],
  };
  const data = { suppliers: [], lots: [], moves: [], history: [], orders: [{ ...toOrder(purchase), due: "2099-01-01" }] };
  const f = summary(data, plan);
  expect(f).toMatchObject({ need: 30, date: "2026-11-30", daysStock: 15, days: 10, minimum: 30, low: true, stock: 15, demand: 28, incoming: 0 });
  expect(f.gap).toBe(13);
  expect(f.prediction).toMatchObject({ method: "Promedio móvil", mape: 12.5 });
});

test("sin pronóstico el resumen indica el motivo y no inventa cifras", () => {
  const f = summary({ suppliers: [], lots: [], moves: [], history: [], orders: [] }, { ...emptyPlan, reason: "Aún no hay historial de consumo" });
  expect(f).toMatchObject({ need: 0, demand: 0, history: [] });
  expect(f.prediction.reason).toBe("Aún no hay historial de consumo");
});

test("traduce los errores de validación de la API", () => {
  expect(messageFrom("Lote no encontrado", 404)).toBe("Lote no encontrado");
  expect(messageFrom([{ loc: ["body", "cantidad_kg"], msg: "Input should be greater than 0" }], 422)).toBe("Revisa la cantidad: Input should be greater than 0");
  expect(messageFrom(undefined, 403)).toMatch(/permiso/);
});

/** jsdom no trae `Response`: basta un objeto con lo que usa el cliente. */
const reply = (body: unknown, status = 200) => ({ ok: status < 400, status, json: async () => body }) as Response;

function fakeServer(routes: Record<string, unknown>) {
  globalThis.fetch = jest.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const path = String(url).replace("http://localhost:8000/api/v1", "");
    const key = (init?.method ?? "GET") + " " + path;
    if (!(key in routes)) return reply({ detail: "Sin ruta " + key }, 500);
    return reply(routes[key]);
  }) as jest.Mock;
}

test("inicia sesión con la API y abre el resumen con la alerta de stock bajo", async () => {
  localStorage.clear();
  const user = { id: 1, nombre: "Ana", email: "demo@originlink.pe", organizacion: { id: 1, tipo: "TOSTADOR", nombre: "Tostaduría Demo", region: "Lima" } };
  fakeServer({
    "POST /auth/login": { access_token: "t" },
    "GET /auth/me": user,
    "GET /proveedores": [], "GET /lotes": [], "GET /compras": [], "GET /movimientos": [],
    "GET /pronostico": { metodo: "PROMEDIO_MOVIL", motivo_metodo: null, mape_referencia: null, historial: [{ semana: "2026-11-16", kg: 14 }],
      pronostico: [0, 1, 2, 3].map((i) => ({ semana: "2026-12-0" + (i + 1), kg: 14 })) },
    "GET /recomendaciones": { fecha_limite_compra: "2026-11-25", cantidad_sugerida_kg: 40, semanas_cobertura_actual: 0.9, dias_cobertura_actual: 6,
      factores: { existencias_kg: 12, plazo_entrega_dias: 10, semanas_cobertura: 2, cantidad_minima_kg: 30, metodo_pronostico: "PROMEDIO_MOVIL" }, explicacion: "" },
    "GET /alertas": [{ tipo: "STOCK_BAJO", mensaje: "x", semanas_cobertura_restantes: 0.9, fecha_limite_compra: "2026-11-25" }],
  });
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><App /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Entrar como tostadora/ }));
  expect(await screen.findByRole("heading", { name: "Resumen de abastecimiento" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Alerta de stock bajo/ })).toBeInTheDocument();
  expect(screen.getByText("Reponer 40 kg")).toBeInTheDocument();
});

test("muestra el error del servidor si las credenciales no sirven", async () => {
  localStorage.clear();
  globalThis.fetch = jest.fn(async () => reply({ detail: "Correo o contraseña incorrectos" }, 401)) as jest.Mock;
  render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><App /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Entrar como cooperativa/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Correo o contraseña incorrectos");
});
