import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { balance, buy, forecast, move, receive, seed } from "./lib/demo";

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
  expect(forecast(purchased, 6).need).toBe(forecast(initial, 6).need - 30);
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
  fireEvent.click(
    screen.getByRole("button", { name: /Entrar como tostadora/ }),
  );
  expect(
    screen.getByRole("heading", { name: "Resumen de abastecimiento" }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Alerta de stock bajo/ }),
  ).toBeInTheDocument();
});
