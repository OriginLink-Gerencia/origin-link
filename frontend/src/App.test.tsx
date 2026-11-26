import { webcrypto } from "node:crypto";
import { TextEncoder } from "node:util";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { balance, buy, forecast, move, receive, seed } from "./lib/demo";
import { createInvitation, initialStore, STORE } from "./lib/workspaces";

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

test("el acceso principal lleva al alta de proveedor con un enlace anterior y consume la invitación", async () => {
  const store = setupInvitations();
  const roaster = store.spaces[0];
  const entry = createInvitation({
    id: 850,
    name: "Café de prueba",
    email: "equipo@example.com",
    region: "",
    linked: false,
    invited: false,
  });
  roaster.suppliers.push(entry);
  localStorage.setItem(STORE, JSON.stringify(store));
  renderPilot();
  fireEvent.click(
    screen.getByRole("link", {
      name: "Crear cuenta de proveedor o abrir invitación",
    }),
  );
  expect(screen.queryByLabelText("Contraseña")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Enlace o código de invitación"), {
    target: {
      value: window.location.origin + "/invitacion?token=" + entry.token,
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Abrir invitación" }));
  expect(screen.getByLabelText("Correo electrónico")).toHaveValue(entry.email);
  fireEvent.change(screen.getByLabelText("Contraseña"), {
    target: { value: "cafeverde123" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Crear cuenta de proveedor y aceptar" }),
  );
  expect(
    await screen.findByRole("heading", { name: "Vínculos y pedidos" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: roaster.name }),
  ).toBeInTheDocument();
  const saved = JSON.parse(localStorage.getItem(STORE)!);
  expect(saved.accounts).toEqual([
    expect.objectContaining({ role: "cooperativa", email: entry.email }),
  ]);
  expect(
    saved.spaces[0].suppliers.find((p: { id: number }) => p.id === entry.id),
  ).toMatchObject({ linked: true, invited: false });
  expect(
    saved.spaces[0].suppliers.find((p: { id: number }) => p.id === entry.id)
      .token,
  ).toBeUndefined();
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

test("un enlace directo rechaza otra cuenta y permite entrar y aceptar con la cuenta invitada", async () => {
  const store = setupInvitations();
  const entry = createInvitation({
    id: 852,
    name: "Cooperativa invitada",
    email: "ventas5@cooperativa-demo.pe",
    region: "",
    linked: false,
    invited: false,
  });
  store.spaces[1].suppliers.push(entry);
  localStorage.setItem(STORE, JSON.stringify(store));
  sessionStorage.setItem(
    "ol.session.v2",
    JSON.stringify({
      role: "cooperativa",
      id: 104,
      expires: Date.now() + 60000,
    }),
  );
  renderPilot("/invitacion/" + entry.token);
  fireEvent.click(screen.getByRole("button", { name: "Aceptar invitación" }));
  expect(
    screen.getByText("Usa la cuenta del proveedor invitado."),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Usar otra cuenta" }));
  expect(
    screen.getByRole("button", { name: "Entrar y aceptar" }),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Contraseña"), {
    target: { value: "OriginLink2026!" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Entrar y aceptar" }));
  expect(
    await screen.findByRole("heading", { name: store.spaces[1].name }),
  ).toBeInTheDocument();
  expect(JSON.parse(localStorage.getItem(STORE)!).accounts).toHaveLength(0);
});
