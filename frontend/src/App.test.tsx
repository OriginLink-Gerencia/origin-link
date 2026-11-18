import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

beforeEach(() => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: "ok", app: "Origin Link API", environment: "test" }),
  }) as jest.Mock;
});

test("muestra el panel del tostador y el estado de la API", async () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  expect(screen.getByRole("heading", { name: /panel del tostador/i })).toBeInTheDocument();
  expect(await screen.findByText(/ok \(test\)/i)).toBeInTheDocument();
});
