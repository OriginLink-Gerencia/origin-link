import database from "../../db.json";
import {
  KEY,
  loadDemo,
  nextId,
  type Data,
  type Lot,
  type Role,
  type Supplier,
} from "./demo";

export type Identity = { role: Role; id: number };
export type Space = Omit<Data, "lots"> & {
  id: number;
  name: string;
  region: string;
  email?: string;
  demo?: boolean;
};
type Credential = Identity & {
  name?: string;
  email: string;
  salt: string;
  hash: string;
};
export type Store = { spaces: Space[]; lots: Lot[]; accounts: Credential[] };
export const STORE = "originlink.piloto.v2";
export const DEMO_PASSWORD = "OriginLink2026!";
const empty = (): Data => ({
  suppliers: [],
  lots: [],
  moves: [],
  orders: [],
  history: [],
});
export function initialStore(): Store {
  const pilot = JSON.parse(JSON.stringify(database.pilot)) as Omit<
    Store,
    "accounts"
  >;
  return { ...pilot, accounts: [] };
}
export function loadStore(): Store {
  const raw = localStorage.getItem(STORE);
  if (raw) return JSON.parse(raw) as Store;
  const store = initialStore();
  if (localStorage.getItem(KEY)) {
    const legacy = loadDemo();
    const { lots, ...rest } = legacy;
    store.spaces.push({
      ...rest,
      id: 5,
      name: "Tostadora Andina · piloto anterior",
      region: "Lima",
      demo: true,
    });
    store.lots.push(...lots);
  }
  return store;
}
export function links(store: Store, supplier: number) {
  const email = supplierEmail(store, supplier);
  return store.spaces.flatMap(({ id, name, region, suppliers }) => {
    return suppliers
      .filter((entry) =>
        entry.linked
          ? entry.id === supplier
          : isPending(entry) &&
            (entry.email
              ? Boolean(email && normalize(entry.email) === email)
              : entry.id === supplier),
      )
      .map((entry) => ({ id, name, region, entry }));
  });
}
export function scoped(store: Store, user: Identity | null): Data {
  if (!user) return empty();
  const nextLotId = nextId(store.lots);
  if (user.role === "tostadora") {
    const space = store.spaces.find((s) => s.id === user.id);
    if (!space) return empty();
    const lots = store.lots.filter((l) =>
      l.owner
        ? l.owner === space.id
        : space.suppliers.some((s) => s.id === l.supplier && s.linked),
    );
    return {
      nextLotId,
      nextOrderId: nextId(store.spaces.flatMap((s) => s.orders)),
      organization: space.id,
      suppliers: space.suppliers,
      moves: space.moves,
      history: space.history,
      orders: space.orders,
      lots,
    };
  }
  const relations = links(store, user.id);
  const own =
    relations.find((r) => r.entry.linked)?.entry ?? relations[0]?.entry;
  const lots = store.lots.filter((l) => !l.owner && l.supplier === user.id);
  const orders = store.spaces
    .filter((s) => relations.some((r) => r.id === s.id && r.entry.linked))
    .flatMap((s) =>
      s.orders
        .filter((o) => lots.some((l) => l.id === o.lot))
        .map((o) => ({ ...o, roaster: s.name, roasterId: s.id })),
    );
  return { ...empty(), nextLotId, lots, orders, suppliers: own ? [own] : [] };
}
export function applyScoped(
  store: Store,
  user: Identity,
  change: (d: Data) => Data,
): Store {
  const current = scoped(store, user),
    next = change(current);
  const lots =
    next.lots === current.lots
      ? store.lots
      : [
          ...store.lots.map((l) => next.lots.find((n) => n.id === l.id) ?? l),
          ...next.lots.filter(
            (l) => !store.lots.some((old) => old.id === l.id),
          ),
        ];
  const spaces = store.spaces.map((s) =>
    user.role === "tostadora" && s.id === user.id
      ? {
          ...s,
          suppliers: next.suppliers,
          orders: next.orders,
          moves: next.moves,
          history: next.history,
        }
      : s,
  );
  return { ...store, spaces, lots };
}
function demoSupplierAccounts(store: Store) {
  const providers: Pick<Supplier, "id" | "name" | "email" | "region">[] = [
    ...database.pilot.providerAccounts,
  ];
  const legacy = store.spaces.find((s) => s.id === 5 && s.demo);
  if (legacy)
    providers.push(
      ...legacy.suppliers.filter(
        (s) => s.linked && database.suppliers.some((p) => p.id === s.id),
      ),
    );
  return providers;
}

export function demoSuppliers(store: Store) {
  return demoSupplierAccounts(store).sort(
    (a, b) => links(store, b.id).length - links(store, a.id).length,
  );
}
function isPending(entry: Supplier) {
  return (
    !entry.linked &&
    entry.invited &&
    Boolean(entry.token) &&
    (entry.expires ?? 0) > Date.now()
  );
}

export function invitation(store: Store, token: string) {
  for (const space of store.spaces) {
    const entry = space.suppliers.find(
      (s) => isPending(s) && s.token === token,
    );
    if (entry) return { space, entry };
  }
  throw Error("Invitación no válida. Pide una nueva a la tostadora.");
}
export function createInvitation(s: Supplier) {
  if (s.linked) throw Error("El proveedor ya está vinculado.");
  return {
    ...s,
    invited: true,
    token: crypto.randomUUID(),
    expires: Date.now() + 7 * 86400000,
  };
}
export function accept(store: Store, token: string, id: number) {
  const { space, entry } = invitation(store, token);
  if (space.suppliers.some((s) => s.id === id && s !== entry))
    throw Error("Ya existe una relación con este proveedor.");
  return {
    ...store,
    spaces: store.spaces.map((s) =>
      s.id !== space.id
        ? s
        : {
            ...s,
            suppliers: s.suppliers.map((p) =>
              p !== entry
                ? p
                : {
                    ...p,
                    id,
                    linked: true,
                    invited: false,
                    token: undefined,
                    expires: undefined,
                  },
            ),
          },
    ),
    lots: store.lots.map((l) =>
      l.owner === space.id && l.supplier === entry.id
        ? { ...l, supplier: id }
        : l,
    ),
  };
}
const normalize = (s: string) => s.trim().toLowerCase();
function supplierEmail(store: Store, id: number) {
  const account = store.accounts.find(
    (a) => a.role === "cooperativa" && a.id === id,
  );
  const demo = demoSupplierAccounts(store).find((a) => a.id === id);
  return normalize(account?.email ?? demo?.email ?? "");
}

export function acceptAsSupplier(store: Store, token: string, user: Identity) {
  const { entry } = invitation(store, token);
  if (
    user.role !== "cooperativa" ||
    (entry.email && normalize(entry.email) !== supplierEmail(store, user.id))
  )
    throw Error("Usa la cuenta del proveedor invitado.");
  return accept(store, token, user.id);
}

export function invitationHasAccount(store: Store, entry: Supplier) {
  const email = entry.email && normalize(entry.email);
  return (
    store.accounts.some(
      (a) =>
        a.role === "cooperativa" &&
        (a.id === entry.id || Boolean(email && a.email === email)),
    ) ||
    demoSupplierAccounts(store).some(
      (a) =>
        a.id === entry.id ||
        Boolean(email && normalize(a.email ?? "") === email),
    )
  );
}
async function digest(password: string, salt: string) {
  const enc = new TextEncoder(),
    key = await crypto.subtle.importKey(
      "raw",
      enc.encode(password),
      "PBKDF2",
      false,
      ["deriveBits"],
    );
  const bits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: enc.encode(salt),
      iterations: 100000,
      hash: "SHA-256",
    },
    key,
    256,
  );
  return Array.from(new Uint8Array(bits), (b) =>
    b.toString(16).padStart(2, "0"),
  ).join("");
}
function seededAccount(store: Store, email: string): Identity | undefined {
  const space = store.spaces.find((s) => s.demo && s.email === email);
  if (space) return { role: "tostadora", id: space.id };
  const supplier = demoSuppliers(store).find((s) => s.email === email);
  if (supplier) return { role: "cooperativa", id: supplier.id };
}
export async function authenticate(
  store: Store,
  email: string,
  password: string,
): Promise<Identity> {
  email = normalize(email);
  const existing = store.accounts.find((a) => a.email === email);
  if (existing && (await digest(password, existing.salt)) === existing.hash)
    return { id: existing.id, role: existing.role };
  const demo = seededAccount(store, email);
  if (demo && password === DEMO_PASSWORD) return demo;
  throw Error("Correo o contraseña incorrectos");
}
export async function register(
  store: Store,
  name: string,
  email: string,
  password: string,
  token?: string,
) {
  email = normalize(email);
  if (
    !name.trim() ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ||
    password.length < 8
  )
    throw Error(
      "Completa el nombre, el correo y una contraseña de al menos 8 caracteres.",
    );
  if (
    store.accounts.some((a) => a.email === email) ||
    seededAccount(store, email)
  )
    throw Error("Ya existe una cuenta con este correo");
  const entry =
    token !== undefined ? invitation(store, token).entry : undefined;
  if (entry?.email && normalize(entry.email) !== email)
    throw Error("Usa el correo del proveedor invitado.");
  if (entry && invitationHasAccount(store, entry))
    throw Error(
      "Esta cooperativa ya tiene cuenta. Inicia sesión para aceptar el vínculo.",
    );
  const user: Identity = {
    role: entry ? "cooperativa" : "tostadora",
    id: entry?.id ?? Date.now(),
  };
  let next =
    token !== undefined
      ? accept(store, token, user.id)
      : {
          ...store,
          spaces: [
            ...store.spaces,
            { ...empty(), id: user.id, name: name.trim(), region: "", email },
          ],
        };
  const salt = crypto.randomUUID(),
    hash = await digest(password, salt);
  next = {
    ...next,
    accounts: [
      ...next.accounts,
      { ...user, name: name.trim(), email, salt, hash },
    ],
  };
  return { store: next, user };
}
