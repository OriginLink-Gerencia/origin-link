// Respuestas reales de la API (capturadas con `python -m app.seed_demo` y el servidor en marcha): si el backend
// cambia un campo, estas pruebas fallan antes de que falle la pantalla.
import { balance, ownLots, pending, visibleLots } from "./demo";
import { toLot, toMovement, toOrder, toReceivedOrder, toSupplier, type ForecastDTO, type LotDTO, type MovementDTO, type PurchaseDTO, type ReceivedOrderDTO, type RecommendationDTO, type SupplierDTO } from "./backend";
import { summary } from "./plan";
import proveedores from "../test/api/roaster_proveedores.json";
import lotes from "../test/api/roaster_lotes.json";
import compras from "../test/api/roaster_compras.json";
import movimientos from "../test/api/roaster_movimientos.json";
import pronostico from "../test/api/roaster_pronostico.json";
import recomendaciones from "../test/api/roaster_recomendaciones.json";
import alertas from "../test/api/roaster_alertas.json";
import lotesCoop from "../test/api/coop_lotes.json";
import pedidos from "../test/api/coop_pedidos-recibidos.json";

const TOSTADOR = 1;
const data = {
  organization: TOSTADOR,
  suppliers: (proveedores as SupplierDTO[]).map(toSupplier),
  lots: (lotes as LotDTO[]).map((l) => toLot(l, TOSTADOR)),
  orders: (compras as PurchaseDTO[]).map(toOrder),
  moves: (movimientos as MovementDTO[]).map(toMovement),
  history: [],
};

test("el tostador de demostración ve sus lotes: el de la cooperativa vinculada y el que registró a mano", () => {
  expect(visibleLots(data).map((l) => l.code).sort()).toEqual(["DONPEPE-2026-01", "JAEN-2026-07"]);
  const coop = data.suppliers.find((p) => p.linked);
  expect(data.lots.find((l) => l.code === "JAEN-2026-07")?.supplier).toBe(coop?.id);
  expect(data.lots.find((l) => l.code === "DONPEPE-2026-01")?.owner).toBe(TOSTADOR);
});

test("el inventario y las compras de la demostración cuadran", () => {
  expect(balance(data)).toBeGreaterThan(0);
  expect(data.orders.every((o) => pending(o) === 0)).toBe(true); // todas recibidas
  expect(data.orders[0].receipts[0].kg).toBeGreaterThan(0);
});

test("el resumen usa el pronóstico, la recomendación y las alertas reales", () => {
  const plan = {
    forecast: pronostico as ForecastDTO,
    recommendation: recomendaciones as RecommendationDTO,
    alerts: alertas as never[],
    reason: "",
  };
  const f = summary(data, plan);
  expect(f.history).toHaveLength(60);
  expect(f.prediction.values).toHaveLength(4);
  expect(f.prediction.method).toBe("Promedio móvil");
  expect(f.demand).toBeGreaterThan(40);
  expect(f.minimum).toBe(30);
  expect(f.days).toBe(10);
});

test("la cooperativa ve sus lotes y los pedidos de sus tostadoras", () => {
  const cooperativa = 2;
  const own = (lotesCoop as LotDTO[]).map((l) => toLot(l, cooperativa));
  expect(ownLots({ suppliers: [], lots: own, orders: [], moves: [], history: [] }, cooperativa)).toHaveLength(1);
  const orders = (pedidos as ReceivedOrderDTO[]).map(toReceivedOrder);
  expect(orders[0].roaster).toBe("Tostaduría Demo");
  expect(orders.map((o) => o.kg)).toEqual([60, 40]);
});
