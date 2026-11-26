import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Brand, ThemeButton } from "./UI";
import { useDemo } from "../lib/session";
const roastLinks = [
  ["/", "Resumen"],
  ["/inventario", "Inventario"],
  ["/pronostico", "Pronóstico"],
  ["/lotes", "Lotes"],
  ["/compras", "Compras"],
  ["/proveedores", "Proveedores"],
];
export default function Layout() {
  const { pathname } = useLocation();
  const s = useDemo(),
    roast = s.role === "tostadora";
  const name = s.name;
  return (
    <>
      <a className="skip" href="#contenido">
        Ir al contenido
      </a>
      <header className="top">
        <Brand />
        <span className="demo">Piloto</span>
        <ThemeButton />
      </header>
      <div className="shell">
        <aside className="sidebar">
          <div className="org">
            <small>{roast ? "TOSTADORA" : "PROVEEDOR"}</small>
            <strong>{name}</strong>
          </div>
          <nav aria-label="Navegación principal">
            {(roast
              ? roastLinks
              : [
                  ["/", "Vínculos y pedidos"],
                  ["/lotes", "Mis lotes"],
                  ["/publicar", "Publicar lote"],
                ]
            ).map(([to, label]) => (
              <NavLink key={to} to={to} end>
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="tools">
            <button className="quiet" onClick={s.logout}>
              Cerrar sesión
            </button>
          </div>
        </aside>
        <main tabIndex={-1} id="contenido">
          <div role="status" className={s.notice ? "feedback" : ""}>
            {s.notice}
          </div>
          <div className="route-view" key={pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </>
  );
}
