import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
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
    roast = s.role === "tostadora",
    [confirm, setConfirm] = useState(false);
  const name = s.name;
  return (
    <>
      <a className="skip" href="#contenido">
        Ir al contenido
      </a>
      <header className="top">
        <Brand />
        <span className="demo">Piloto · Datos simulados</span>
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
              Cambiar de cuenta
            </button>
            <button className="quiet" onClick={() => setConfirm(true)}>
              Restablecer demo
            </button>
            {confirm && (
              <div className="reset">
                <p>
                  ¿Volver al escenario inicial y borrar los cambios de la
                  entrevista?
                </p>
                <button onClick={s.reset}>Sí, restablecer</button>{" "}
                <button className="secondary" onClick={() => setConfirm(false)}>
                  Cancelar
                </button>
              </div>
            )}
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
