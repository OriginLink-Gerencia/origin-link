import { useCallback, useEffect, useMemo, useState } from "react";
import type { NavigateFunction } from "react-router-dom";
import type { Data, Lot, Role, Supplier } from "./demo";
import { ApiError, request, token } from "./http";
import {
  movementCodes,
  processCodes,
  toLot,
  toMovement,
  toOrder,
  toReceivedOrder,
  toSupplier,
  type AlertDTO,
  type ForecastDTO,
  type LotDTO,
  type MovementDTO,
  type PurchaseDTO,
  type ReceivedOrderDTO,
  type RecommendationDTO,
  type SupplierDTO,
} from "./backend";
import { emptyPlan, type Plan } from "./plan";

type UserDTO = { id: number; nombre: string; email: string; organizacion: { id: number; tipo: "TOSTADOR" | "PROVEEDOR"; nombre: string; region: string | null } };
type Token = { access_token: string };
type Link = { tostador_id: number; tostador: string; vinculado_desde: string };

export type Relation = { id: number; name: string; region: string; entry: Supplier };
export const DEMO_EMAILS = { tostadora: "demo@originlink.pe", cooperativa: "coop@originlink.pe" };
export const DEMO_PASSWORD = "OriginLink2026!";

const emptyData: Data = { suppliers: [], lots: [], moves: [], orders: [], history: [] };
const roleOf = (u: UserDTO | null): Role | null => (u ? (u.organizacion.tipo === "TOSTADOR" ? "tostadora" : "cooperativa") : null);
const today = () => new Date().toLocaleDateString("en-CA");

async function loadRoaster(own: number): Promise<{ data: Data; plan: Plan }> {
  const [suppliers, lots, purchases, moves] = await Promise.all([
    request<SupplierDTO[]>("/proveedores"),
    request<LotDTO[]>("/lotes"),
    request<PurchaseDTO[]>("/compras"),
    request<MovementDTO[]>("/movimientos"),
  ]);
  let plan: Plan = emptyPlan;
  try {
    const [forecast, recommendation, alerts] = await Promise.all([
      request<ForecastDTO>("/pronostico"),
      request<RecommendationDTO>("/recomendaciones"),
      request<AlertDTO[]>("/alertas"),
    ]);
    plan = { forecast, recommendation, alerts, reason: "" };
  } catch (e) {
    // 409: todavía no hay consumo suficiente. Se muestra el motivo en lugar de un error.
    if (!(e instanceof ApiError) || e.status !== 409) throw e;
    plan = { ...emptyPlan, reason: e.message };
  }
  return {
    data: {
      organization: own,
      suppliers: suppliers.map(toSupplier),
      lots: lots.map((l) => toLot(l, own)),
      orders: purchases.map(toOrder),
      moves: moves.map(toMovement).sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id),
      history: plan.forecast?.historial.map((p) => ({ date: p.semana, kg: p.kg })) ?? [],
    },
    plan,
  };
}

async function loadCooperative(own: number): Promise<{ data: Data; relations: Relation[] }> {
  const [links, lots, orders] = await Promise.all([
    request<Link[]>("/vinculos"),
    request<LotDTO[]>("/lotes"),
    request<ReceivedOrderDTO[]>("/pedidos-recibidos"),
  ]);
  const relations = links.map((l) => ({
    id: l.tostador_id,
    name: l.tostador,
    region: "",
    entry: { id: own, name: l.tostador, region: "", linked: true, invited: false } as Supplier,
  }));
  return {
    data: { ...emptyData, lots: lots.map((l) => toLot(l, own)), orders: orders.map(toReceivedOrder), suppliers: relations.slice(0, 1).map((r) => r.entry) },
    relations,
  };
}

export function usePilot(nav: NavigateFunction) {
  const [user, setUser] = useState<UserDTO | null>(null);
  const [booting, setBooting] = useState(() => Boolean(token.get()));
  const [data, setData] = useState<Data>(emptyData);
  const [plan, setPlan] = useState<Plan>(emptyPlan);
  const [relations, setRelations] = useState<Relation[]>([]);
  const [notice, setNotice] = useState("");
  const role = roleOf(user);
  const own = user?.organizacion.id ?? 0;

  const refresh = useCallback(async (u: UserDTO) => {
    if (u.organizacion.tipo === "TOSTADOR") {
      const r = await loadRoaster(u.organizacion.id);
      setData(r.data);
      setPlan(r.plan);
      setRelations([]);
    } else {
      const r = await loadCooperative(u.organizacion.id);
      setData(r.data);
      setPlan(emptyPlan);
      setRelations(r.relations);
    }
  }, []);

  const start = useCallback(
    async (u: UserDTO) => {
      await refresh(u);
      setUser(u);
      setNotice("");
    },
    [refresh],
  );

  useEffect(() => {
    if (!token.get()) return;
    request<UserDTO>("/auth/me")
      .then(start)
      .catch(() => token.clear())
      .finally(() => setBooting(false));
  }, [start]);

  function logout() {
    token.clear();
    setUser(null);
    setData(emptyData);
    setPlan(emptyPlan);
    setRelations([]);
    setNotice("");
    nav("/");
  }

  /** Ejecuta una acción contra la API, recarga los datos y muestra el resultado. Devuelve si salió bien. */
  async function run(action: () => Promise<unknown>, message: string) {
    try {
      if (!user) throw new Error("Vuelve a iniciar sesión.");
      await action();
      await refresh(user);
      setNotice(message);
      return true;
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        logout();
        setNotice(e.message);
      } else setNotice((e as Error).message);
      return false;
    }
  }

  async function credentials(email: string, password: string, name?: string, invitation?: string, person?: string) {
    const clean = email.trim().toLowerCase();
    let session: Token;
    if (name !== undefined) {
      const body = { empresa: name.trim(), nombre: (person ?? name).trim(), email: clean, password };
      session = await request<Token>(invitation ? "/auth/registro-invitacion" : "/auth/registro", {
        method: "POST",
        auth: false,
        body: invitation ? { ...body, token: invitation } : body,
      });
    } else {
      session = await request<Token>("/auth/login", { method: "POST", auth: false, body: { email: clean, password } });
    }
    token.set(session.access_token);
    try {
      if (invitation && name === undefined) await request("/invitaciones/" + encodeURIComponent(invitation) + "/aceptar", { method: "POST" });
      await start(await request<UserDTO>("/auth/me"));
    } catch (e) {
      token.clear();
      throw e;
    }
    nav("/");
  }

  const saveSupplier = (entry: Supplier) =>
    run(
      async () => {
        const body = {
          nombre: entry.name,
          region: entry.region || null,
          contacto_nombre: entry.contact || null,
          contacto_telefono: entry.phone || null,
          contacto_email: entry.email || null,
        };
        if (entry.id) await request("/proveedores/" + entry.id, { method: "PATCH", body });
        else await request("/proveedores", { method: "POST", body });
      },
      "Proveedor guardado.",
    );
  const invite = (id: number) =>
    run(() => request("/proveedores/" + id + "/invitaciones", { method: "POST" }), "Invitación creada. Comparte el enlace con el proveedor.");
  const buy = (lot: number, kg: number, price: number, due: string) =>
    run(
      () =>
        request("/compras", {
          method: "POST",
          body: { lote_id: lot, cantidad_kg: kg, precio_kg: price, fecha_compra: today(), fecha_entrega_acordada: due },
        }),
      "Compra registrada. Cuando llegue el café, registra la recepción.",
    );
  const receive = (order: number, kg: number, note: string) =>
    run(
      () => request("/compras/" + order + "/recepcion", { method: "POST", body: { fecha_recepcion: today(), cantidad_recibida_kg: kg, observaciones: note.trim() || null } }),
      "Recepción guardada. Los kilos recibidos ya están en inventario.",
    );
  const addMovement = (lot: number, kind: keyof typeof movementCodes, kg: number, note: string) =>
    run(
      () => request("/movimientos", { method: "POST", body: { lote_id: lot, tipo: movementCodes[kind], cantidad_kg: kg, fecha: today(), motivo: note.trim() || null } }),
      "Movimiento guardado. Saldo actualizado.",
    );
  const saveLot = (lot: Lot, manual: boolean) =>
    run(
      async () => {
        if (lot.id) {
          // El servidor solo permite cambiar las condiciones de venta de un lote ya publicado.
          await request("/lotes/" + lot.id + "/disponibilidad", {
            method: "PATCH",
            body: { cantidad_disponible_kg: lot.available, precio_kg: lot.price, cantidad_minima_kg: lot.minimum, plazo_entrega_dias: lot.days },
          });
          return;
        }
        await request("/lotes", {
          method: "POST",
          body: {
            proveedor_id: manual ? lot.supplier : null,
            codigo: lot.code,
            region: lot.region,
            finca: lot.farm || null,
            variedad: lot.variety,
            proceso: processCodes[lot.process] ?? "OTRO",
            cosecha: String(lot.harvest),
            altitud_msnm: lot.altitude || null,
            caracteristicas: lot.notes || null,
            cantidad_disponible_kg: lot.available,
            precio_kg: lot.price,
            cantidad_minima_kg: lot.minimum,
            plazo_entrega_dias: lot.days,
          },
        });
      },
      manual ? "Lote privado registrado." : lot.id ? "Lote actualizado para tus tostadoras vinculadas." : "Lote publicado para tus tostadoras vinculadas.",
    );
  async function importConsumption(file: File) {
    const form = new FormData();
    form.append("archivo", file);
    const result = await request<{ semanas_importadas: number; errores: { fila: number; error: string }[] }>("/consumo-historico/importar", { method: "POST", form });
    if (result.errores.length) {
      const shown = result.errores.slice(0, 5).map((e) => `fila ${e.fila}: ${e.error}`);
      throw new Error("No se importó nada. Corrige el archivo: " + shown.join("; ") + (result.errores.length > 5 ? "…" : "."));
    }
    if (user) await refresh(user);
    setNotice(result.semanas_importadas + " semanas importadas.");
  }
  const simulate = (days: number, minimum: number) =>
    request<RecommendationDTO>(`/recomendaciones?plazo_entrega_dias=${days}&cantidad_minima_kg=${minimum}`);
  const acceptLink = (invitation: string) =>
    run(() => request("/invitaciones/" + encodeURIComponent(invitation) + "/aceptar", { method: "POST" }), "Vínculo aceptado.");

  return useMemo(
    () => ({
      data,
      plan,
      role,
      booting,
      supplier: own,
      name: user?.organizacion.nombre ?? "",
      region: user?.organizacion.region ?? "",
      notice,
      setNotice,
      logout,
      relations,
      credentials,
      saveSupplier,
      invite,
      buy,
      receive,
      addMovement,
      saveLot,
      importConsumption,
      simulate,
      acceptLink,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, plan, role, booting, own, user, notice, relations],
  );
}
