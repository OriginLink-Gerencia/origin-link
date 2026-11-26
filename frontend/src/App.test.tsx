import { webcrypto } from "node:crypto";
import { TextEncoder } from "node:util";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { balance, buy, forecast, move, receive, seed } from "./lib/demo";
import {
  createInvitation,
  initialStore,
  loadStore,
  STORE,
} from "./lib/workspaces";

test("reserva café y acredita cada entrega una sola vez", () => {
  const initial = seed(),
    stock = balance(initial);
  const purchased = buy(initial, 1, 30, 31, "2026-12-01"),
    id = purchased.orders[0].id;
  expect(purchased.lots[0].available).toBe(initial.lots[0].available - 30);
  expect(balance(purchased)).toBe(stock);
  const partial = receive(purchased, id, 12, "Primer saco");
  expect(balance(partial)).toBe(stock + 12);
  expect(() => receive(partial, id, 30, "")).toThrow();
  const full = receive(partial, id, 18, "Saldo");
  expect(balance(full)).toBe(stock + 30);
  expect(() => receive(full, id, 1, "")).toThrow();
  expect(() => move(full, 1, "Consumo", 999, "")).toThrow();
  expect(forecast(purchased, 6).gap).toBe(forecast(initial, 6).gap - 30);
});
test("abre el resumen desde el acceso de demostración", () => {
  localStorage.clear();
  render(
    <MemoryRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByText("Probar con datos de demostración"));
  fireEvent.click(
    screen.getByRole("button", { name: /Entrar como tostadora/ }),
  );
  expect(
    screen.getByRole("heading", { name: "Resumen de abastecimiento" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Revisar recomendación/ }),
  ).toBeInTheDocument();
});

test("cambia el acceso a inglés y vuelve a español conservando el formulario", () => {
  localStorage.clear();
  sessionStorage.clear();
  document.documentElement.lang = "es-PE";
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  const email = screen.getByLabelText("Correo electrónico");
  fireEvent.change(email, { target: { value: "prueba@example.com" } });
  fireEvent.click(screen.getByRole("button", { name: "Switch to English" }));
  expect(
    screen.getByRole("heading", { name: "Sign in to your workspace" }),
  ).toBeInTheDocument();
  expect(screen.getByLabelText("Email address")).toHaveValue(
    "prueba@example.com",
  );
  expect(document.documentElement.lang).toBe("en-US");
  fireEvent.click(screen.getByRole("button", { name: "Cambiar a español" }));
  expect(
    screen.getByRole("heading", { name: "Entra a tu espacio" }),
  ).toBeInTheDocument();
});

function setupInvitations() {
  localStorage.clear();
  sessionStorage.clear();
  document.documentElement.lang = "es-PE";
  Object.defineProperty(window, "crypto", {
    value: webcrypto,
    configurable: true,
  });
  Object.defineProperty(globalThis, "TextEncoder", {
    value: TextEncoder,
    configurable: true,
  });
  return initialStore();
}

function renderPilot(entry = "/") {
  render(
    <MemoryRouter
      initialEntries={[entry]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <App />
    </MemoryRouter>,
  );
}

test("Flor de Café recibe la invitación de Horizonte en un piloto guardado y puede aceptarla", () => {
  const previous = setupInvitations();
  previous.spaces = previous.spaces.filter(
    (space) => space.name !== "Tostadora Horizonte",
  );
  localStorage.setItem(STORE, JSON.stringify(previous));
  renderPilot();
  fireEvent.click(screen.getByText("Probar con datos de demostración"));
  fireEvent.change(screen.getByLabelText("Proveedor"), {
    target: { value: "102" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Entrar como cooperativa" }),
  );

  const pending = screen
    .getByRole("heading", { name: "Invitaciones pendientes" })
    .closest("section")!;
  expect(within(pending).getByText("Tostadora Horizonte")).toBeInTheDocument();
  fireEvent.click(
    within(pending).getByRole("button", { name: "Aceptar invitación" }),
  );
  expect(
    screen.getByRole("heading", { name: "Tostadora Horizonte" }),
  ).toBeInTheDocument();
  expect(
    within(pending).queryByText("Tostadora Horizonte"),
  ).not.toBeInTheDocument();
  expect(
    loadStore().spaces.find((space) => space.name === "Tostadora Horizonte")
      ?.suppliers[0],
  ).toMatchObject({ id: 102, linked: true, invited: false });
});

test("un enlace de invitación anterior vuelve al acceso normal", () => {
  const store = setupInvitations();
  localStorage.setItem(STORE, JSON.stringify(store));
  renderPilot("/invitacion/demo-horizonte-flor-de-cafe");
  expect(
    screen.getByRole("heading", { name: "Entra a tu espacio" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: "Crear cuenta de proveedor" }),
  ).toBeInTheDocument();
  expect(
    screen.queryByLabelText("Enlace o código de invitación"),
  ).not.toBeInTheDocument();
  expect(loadStore()).toEqual(store);
});

test("un proveedor se registra sin invitación y puede aceptar una que reciba después", async () => {
  setupInvitations();
  renderPilot();
  fireEvent.click(
    screen.getByRole("link", { name: "Crear cuenta de proveedor" }),
  );
  expect(
    screen.queryByLabelText("Enlace o código de invitación"),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Nombre de la organización"), {
    target: { value: "Cooperativa Nueva" },
  });
  fireEvent.change(screen.getByLabelText("Correo electrónico"), {
    target: { value: "nueva@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Contraseña"), {
    target: { value: "cafe-verde-123" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Crear cuenta de proveedor" }),
  );

  expect(
    await screen.findByRole("heading", { name: "Vínculos y pedidos" }),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Aún no tienes tostadoras vinculadas."),
  ).toBeInTheDocument();
  const store = loadStore();
  expect(store.spaces).toHaveLength(initialStore().spaces.length);
  expect(store.accounts).toEqual([
    expect.objectContaining({
      role: "cooperativa",
      email: "nueva@example.com",
    }),
  ]);

  fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
  const roaster = store.spaces[0];
  roaster.suppliers.push(
    createInvitation({
      id: 853,
      name: "Cooperativa Nueva",
      email: "nueva@example.com",
      region: "",
      linked: false,
      invited: false,
    }),
  );
  localStorage.setItem(STORE, JSON.stringify(store));
  fireEvent(window, new StorageEvent("storage", { key: STORE }));
  fireEvent.change(screen.getByLabelText("Correo electrónico"), {
    target: { value: "nueva@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Contraseña"), {
    target: { value: "cafe-verde-123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));

  const acceptButton = await screen.findByRole("button", {
    name: "Aceptar invitación",
  });
  expect(
    screen.getByText("Aún no tienes tostadoras vinculadas."),
  ).toBeInTheDocument();
  fireEvent.click(acceptButton);
  expect(
    screen.getByRole("heading", { name: roaster.name }),
  ).toBeInTheDocument();
});

test("un proveedor existente acepta desde su panel aunque la tostadora usara otro identificador", () => {
  const store = setupInvitations();
  const entry = createInvitation({
    id: 851,
    name: "Alias de la cooperativa",
    email: " VENTAS5@COOPERATIVA-DEMO.PE ",
    region: "",
    linked: false,
    invited: false,
  });
  const roaster = store.spaces[1];
  roaster.suppliers.push(entry);
  localStorage.setItem(STORE, JSON.stringify(store));
  sessionStorage.setItem(
    "ol.session.v2",
    JSON.stringify({
      role: "cooperativa",
      id: 105,
      expires: Date.now() + 60000,
    }),
  );
  renderPilot();
  const pending = screen
    .getByRole("heading", { name: "Invitaciones pendientes" })
    .closest("section")!;
  expect(within(pending).getByText(roaster.name)).toBeInTheDocument();
  fireEvent.click(
    within(pending).getByRole("button", { name: "Aceptar invitación" }),
  );
  expect(screen.getByText("Vínculo aceptado.")).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: roaster.name }),
  ).toBeInTheDocument();
  expect(
    within(pending).queryByRole("button", { name: "Aceptar invitación" }),
  ).not.toBeInTheDocument();
});
