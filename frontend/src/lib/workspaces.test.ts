import { webcrypto } from "node:crypto";
import { TextEncoder } from "node:util";
import {
  accept,
  acceptAsSupplier,
  applyScoped,
  authenticate,
  createInvitation,
  demoSuppliers,
  initialStore,
  invitation,
  links,
  loadStore,
  register,
  scoped,
  STORE,
} from "./workspaces";
import {
  balance,
  buy,
  forecast,
  KEY,
  move,
  pending,
  receive,
  received,
  seed,
  setLot,
} from "./demo";
import { weeklyRows } from "./consumption";
import { performance } from "./performance";

const roast = (id: number) => ({ role: "tostadora" as const, id });
const coop = (id: number) => ({ role: "cooperativa" as const, id });
beforeAll(() => {
  Object.defineProperty(window, "crypto", {
    value: webcrypto,
    configurable: true,
  });
  Object.defineProperty(globalThis, "TextEncoder", {
    value: TextEncoder,
    configurable: true,
  });
});
beforeEach(() => localStorage.clear());

test("semilla determinista y saldos oficiales de las cuatro tostadoras", () => {
  const store = initialStore();
  expect(initialStore().spaces.slice(0, 4)).toEqual(store.spaces.slice(0, 4));
  expect(
    store.spaces.slice(0, 4).map((s) => balance(scoped(store, roast(s.id)))),
  ).toEqual([12.14, 16.78, 28.44, 3.32]);
  expect(
    store.spaces.every((s) =>
      scoped(store, roast(s.id)).orders.every((o) =>
        scoped(store, roast(s.id)).lots.some((l) => l.id === o.lot),
      ),
    ),
  ).toBe(true);
});
test("la cooperativa ve sus cuatro clientes y sus pedidos, sin sus inventarios privados", () => {
  const store = initialStore(),
    supplier = demoSuppliers(store)[0],
    view = scoped(store, coop(supplier.id));
  expect(
    links(store, supplier.id)
      .filter(({ entry }) => entry.linked)
      .map((s) => s.name),
  ).toEqual(store.spaces.slice(0, 4).map((s) => s.name));
  expect(view.moves).toEqual([]);
  expect(view.history).toEqual([]);
  expect(view.orders.length).toBeGreaterThan(1);
  expect(
    view.orders.every((o) =>
      view.lots.some((l) => l.id === o.lot && l.supplier === supplier.id),
    ),
  ).toBe(true);
  expect(
    scoped(store, roast(2)).orders.every(
      (o) => !scoped(store, roast(1)).orders.some((other) => other.id === o.id),
    ),
  ).toBe(true);
});
test("alta, correo duplicado, autenticación y espacio privado vacío", async () => {
  const { store, user } = await register(
    initialStore(),
    "Nueva tostadora",
    " ANA@ejemplo.pe ",
    "cafeverde1",
  );
  expect(scoped(store, user).lots).toEqual([]);
  expect(store.accounts[0].hash).not.toContain("cafeverde1");
  expect(await authenticate(store, "ana@ejemplo.pe", "cafeverde1")).toEqual(
    user,
  );
  await expect(authenticate(store, "ana@ejemplo.pe", "otra")).rejects.toThrow(
    "Correo o contraseña incorrectos",
  );
  await expect(
    register(store, "Otra", "ana@ejemplo.pe", "cafeverde2"),
  ).rejects.toThrow("Ya existe una cuenta");
  await expect(register(store, "Otra", "otra@ejemplo.pe", "1")).rejects.toThrow(
    "8 caracteres",
  );
});
test("invitación expira, se usa una vez y la misma cooperativa puede aceptar un segundo vínculo", async () => {
  let store = initialStore();
  const entry = store.spaces[0].suppliers.find((p) => !p.linked)!;
  const issue = createInvitation(entry);
  store = applyScoped(store, roast(1), (d) => ({
    ...d,
    suppliers: d.suppliers.map((p) => (p.id === entry.id ? issue : p)),
  }));
  expect(issue.expires! - Date.now()).toBeCloseTo(7 * 86400000, -3);
  const expiry = {
    ...store,
    spaces: store.spaces.map((s) => ({
      ...s,
      suppliers: s.suppliers.map((p) => ({ ...p, expires: 0 })),
    })),
  };
  expect(() => invitation(expiry, issue.token)).toThrow("Invitación no válida");
  const account = await register(
    store,
    entry.name,
    entry.email!,
    "cafeverde1",
    "cooperativa",
  );
  expect(() =>
    acceptAsSupplier(account.store, issue.token, roast(1)),
  ).toThrow();
  expect(() =>
    acceptAsSupplier(account.store, issue.token, coop(105)),
  ).toThrow();
  const linked = acceptAsSupplier(account.store, issue.token, account.user);
  expect(() => invitation(linked, issue.token)).toThrow();
  const next = createInvitation({ ...entry, id: 888 });
  const another = applyScoped(linked, roast(2), (d) => ({
    ...d,
    suppliers: [...d.suppliers, next],
  }));
  expect(
    links(accept(another, next.token, account.user.id), account.user.id).map(
      (r) => r.id,
    ),
  ).toEqual([1, 2]);
});
test("lote manual sigue privado después de vincular, publicación y compra actualizan el catálogo compartido", () => {
  let store = initialStore();
  const d = scoped(store, roast(1)),
    provider = d.suppliers.find((s) => !s.linked)!;
  store = applyScoped(store, roast(1), (v) =>
    setLot(v, provider.id, {
      ...d.lots[0],
      id: 0,
      code: "PRIVADO",
      supplier: provider.id,
      owner: 1,
    }),
  );
  const invite = createInvitation(provider);
  store = applyScoped(store, roast(1), (v) => ({
    ...v,
    suppliers: v.suppliers.map((p) => (p.id === provider.id ? invite : p)),
  }));
  store = accept(store, invite.token, provider.id);
  expect(scoped(store, roast(1)).lots.some((l) => l.code === "PRIVADO")).toBe(
    true,
  );
  expect(
    scoped(store, coop(provider.id)).lots.some((l) => l.code === "PRIVADO"),
  ).toBe(false);
  expect(scoped(store, roast(2)).lots.some((l) => l.code === "PRIVADO")).toBe(
    false,
  );
  const supplier = demoSuppliers(store)[0].id;
  store = applyScoped(store, coop(supplier), (v) =>
    setLot(v, supplier, {
      ...v.lots[0],
      id: 0,
      code: "NUEVO",
      available: 60,
      minimum: 10,
    }),
  );
  const lot = scoped(store, roast(2)).lots.find((l) => l.code === "NUEVO")!;
  expect(() =>
    buy(scoped(store, roast(2)), lot.id, 61, 20, "2026-12-01"),
  ).toThrow("supera lo disponible");
  store = applyScoped(store, roast(2), (v) =>
    buy(v, lot.id, 60, 20, "2026-12-01"),
  );
  expect(
    scoped(store, roast(1)).lots.find((l) => l.id === lot.id)?.available,
  ).toBe(0);
  expect(
    scoped(store, coop(supplier)).orders.some(
      (o) => o.lot === lot.id && o.roasterId === 2,
    ),
  ).toBe(true);
});
test("recepción corta cerrada acredita el peso real y alimenta cumplimiento y trazabilidad", () => {
  const p = buy(seed(), 1, 60, 31, "2026-12-01"),
    id = p.orders[0].id;
  const done = receive(p, id, 55, "Faltó un saco", true),
    order = done.orders[0];
  expect(received(order) - order.kg).toBe(-5);
  expect(pending(order)).toBe(0);
  expect(balance(done) - balance(p)).toBe(55);
  expect(() => receive(done, id, 5, "")).toThrow();
  expect(performance([order])).toEqual({
    weight: "91.7%",
    onTime: "100%",
    count: 1,
  });
  expect(performance([])).toBeNull();
  expect(() => move(done, 1, "Ajuste", -1, "")).toThrow("motivo");
  expect(balance(move(done, 1, "Consumo", 8, ""), 1)).toBe(
    balance(done, 1) - 8,
  );
});
test("importación atómica por semana y mensaje de todas las filas inválidas", () => {
  const header = ["fecha", "kg_consumidos"];
  expect(
    weeklyRows([
      header,
      ["2026-11-17", "2.25"],
      [new Date("2026-11-19T00:00:00Z"), 3],
    ]),
  ).toEqual([{ date: "2026-11-16", kg: 5.25 }]);
  expect(() =>
    weeklyRows([header, ["2026-02-30", 1], ["2026-11-17", -1]]),
  ).toThrow("2, 3");
});
test("selección del método por validación, respaldo y recomendación sin elegir proveedor", () => {
  const store = initialStore(),
    tcn = forecast(scoped(store, roast(1))),
    baseline = forecast(scoped(store, roast(3)));
  expect(tcn.prediction.method).toBe("TCN global");
  expect(new Set(tcn.prediction.values).size).toBeGreaterThan(1);
  expect(baseline.prediction.method).toBe("Promedio móvil");
  const d = {
    ...seed(),
    history: [{ date: "2026-11-16", kg: 20 }],
    orders: [],
    moves: [],
  };
  const cold = forecast(d);
  expect(cold.prediction.reason).toContain("insuficiente");
  expect([cold.days, cold.minimum, cold.need, cold.low]).toEqual([
    7,
    0,
    60,
    true,
  ]);
  expect(forecast(d, 9, 25).need).toBe(75);
  expect(
    forecast({
      ...d,
      moves: [
        {
          id: 1,
          lot: 1,
          kind: "Entrada",
          kg: 100,
          date: "2026-11-25",
          note: "",
        },
      ],
    }).low,
  ).toBe(false);
});
test("conserva el piloto anterior sin mezclar sus compras y lotes con la nueva semilla", () => {
  localStorage.setItem(KEY, JSON.stringify(seed()));
  const store = loadStore(),
    legacy = scoped(store, roast(5));
  expect(balance(legacy)).toBe(balance(seed()));
  expect(legacy.orders).toEqual(seed().orders);
  localStorage.setItem(STORE, JSON.stringify(store));
  expect(loadStore().spaces).toHaveLength(6);
});
