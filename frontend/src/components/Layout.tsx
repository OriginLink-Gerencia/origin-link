import { NavLink, Outlet } from "react-router-dom";

// Menú del MVP: un enlace por módulo del flujo principal.
const enlaces = [
  { to: "/", label: "Inicio" },
  { to: "/proveedores", label: "Proveedores" },
  { to: "/lotes", label: "Lotes" },
  { to: "/compras", label: "Compras" },
  { to: "/inventario", label: "Inventario" },
  { to: "/pronostico", label: "Pronóstico" },
];

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
          <span className="text-lg font-semibold text-amber-800">Origin Link</span>
          {enlaces.map((e) => (
            <NavLink
              key={e.to}
              to={e.to}
              end={e.to === "/"}
              className={({ isActive }) =>
                isActive ? "font-medium text-amber-800" : "text-stone-600 hover:text-stone-900"
              }
            >
              {e.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
