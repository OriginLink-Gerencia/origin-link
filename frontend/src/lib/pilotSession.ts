import { useEffect, useState } from "react";
import type { NavigateFunction } from "react-router-dom";
import { KEY, type Data, type Role, type Supplier } from "./demo";
import {
  acceptAsSupplier,
  applyScoped,
  authenticate,
  demoSuppliers,
  initialStore,
  links,
  loadStore,
  register,
  scoped,
  STORE,
  type Identity,
  type Store,
} from "./workspaces";
const SESSION = "ol.session.v2";
function currentUser(): (Identity & { expires: number }) | null {
  try {
    const u = JSON.parse(sessionStorage.getItem(SESSION) || "null");
    return u?.expires > Date.now() ? u : null;
  } catch {
    return null;
  }
}
export function usePilot(nav: NavigateFunction) {
  const [store, setStore] = useState(loadStore),
    [user, setUser] = useState(currentUser),
    [notice, setNotice] = useState("");
  useEffect(() => {
    function sync(e: StorageEvent) {
      if (e.key === STORE) {
        setStore(loadStore());
      }
    }
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  useEffect(() => {
    if (!user) return;
    const timer = window.setTimeout(
      () => {
        sessionStorage.removeItem(SESSION);
        setUser(null);
        setNotice("La sesión ha vencido.");
      },
      Math.max(0, user.expires - Date.now()),
    );
    return () => window.clearTimeout(timer);
  }, [user]);
  function commit(next: Store) {
    localStorage.setItem(STORE, JSON.stringify(next));
    setStore(next);
  }
  function begin(u: Identity) {
    const session = {
      role: u.role,
      id: u.id,
      expires: Date.now() + 8 * 3600000,
    };
    sessionStorage.setItem(SESSION, JSON.stringify(session));
    setUser(session);
    setNotice("");
    nav("/");
  }
  function logout() {
    sessionStorage.removeItem(SESSION);
    setUser(null);
    setNotice("");
    nav("/");
  }
  function update(change: (d: Data) => Data, message: string) {
    try {
      if (!user || !currentUser()) throw Error("Vuelve a iniciar sesión.");
      commit(applyScoped(loadStore(), user, change));
      setNotice(message);
      return true;
    } catch (e) {
      setNotice((e as Error).message);
      return false;
    }
  }
  const demos = demoSuppliers(store);
  const space = store.spaces.find(
    (s) => s.id === user?.id && user.role === "tostadora",
  );
  function saveSupplier(entry: Supplier) {
    const source = loadStore();
    const identity =
      entry.email &&
      [
        ...demoSuppliers(source),
        ...source.accounts.filter((a) => a.role === "cooperativa"),
        ...source.spaces.flatMap((s) => s.suppliers),
      ].find((p) => p.email?.toLowerCase() === entry.email?.toLowerCase());
    return update((d) => {
      if (!entry.name.trim())
        throw Error("El nombre del proveedor es obligatorio.");
      const prior = d.suppliers.find((p) => p.id === entry.id);
      const changed = prior && prior.email !== entry.email;
      if (
        changed &&
        (prior.linked || (prior.invited && (prior.expires ?? 0) > Date.now()))
      )
        throw Error(
          "El correo está asociado a un vínculo o invitación vigente.",
        );
      const id =
        (!changed && entry.id) || (identity && identity.id) || Date.now();
      if (d.suppliers.some((p) => p.id === id && p !== prior))
        throw Error("El proveedor ya está en tu directorio.");
      const saved = {
        ...entry,
        id,
        ...(changed
          ? { invited: false, token: undefined, expires: undefined }
          : {}),
      };
      return {
        ...d,
        suppliers: prior
          ? d.suppliers.map((p) => (p === prior ? saved : p))
          : [...d.suppliers, saved],
        lots:
          prior && prior.id !== id
            ? d.lots.map((l) =>
                l.owner === d.organization && l.supplier === prior.id
                  ? { ...l, supplier: id }
                  : l,
              )
            : d.lots,
      };
    }, "Proveedor guardado.");
  }
  const relations = user?.role === "cooperativa" ? links(store, user.id) : [];
  return {
    data: scoped(store, user),
    role: user?.role ?? null,
    supplier: user?.id ?? 0,
    name:
      space?.name ??
      store.accounts.find((a) => a.role === user?.role && a.id === user?.id)
        ?.name ??
      demos.find((p) => p.id === user?.id)?.name ??
      relations[0]?.entry.name ??
      "",
    region: space?.region ?? "",
    notice,
    update,
    logout,
    saveSupplier,
    relations,
    demoRoasters: store.spaces
      .filter((s) => s.demo)
      .map(({ id, name }) => ({ id, name })),
    demoSuppliers: demos,
    login: (role: Role, id: number) => {
      if (
        role === "tostadora"
          ? store.spaces.some((s) => s.id === id && s.demo)
          : demos.some((s) => s.id === id)
      )
        begin({ role, id });
    },
    async credentials(
      email: string,
      password: string,
      name?: string,
      role?: Role,
    ) {
      const raw = localStorage.getItem(STORE),
        source = loadStore();
      if (name === undefined) {
        begin(await authenticate(source, email, password));
        return;
      }
      const result = await register(source, name, email, password, role);
      if (raw !== localStorage.getItem(STORE))
        throw Error(
          "Los datos cambiaron en otra pestaña. Vuelve a intentarlo.",
        );
      commit(result.store);
      begin(result.user);
    },
    acceptLink: (token: string) => {
      try {
        const active = currentUser();
        if (!active) throw Error("Vuelve a iniciar sesión.");
        commit(acceptAsSupplier(loadStore(), token, active));
        setNotice("Vínculo aceptado.");
        return true;
      } catch (e) {
        setNotice((e as Error).message);
        return false;
      }
    },
    canReset:
      !!user &&
      !store.accounts.length &&
      (space?.demo || demos.some((s) => s.id === user.id)),
    reset: () => {
      if (loadStore().accounts.length) {
        setNotice("Hay cuentas registradas en este navegador.");
        return;
      }
      commit(initialStore());
      localStorage.removeItem(KEY);
      logout();
      setNotice("Demo restablecida.");
    },
  };
}
