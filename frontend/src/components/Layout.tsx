import LanguageButton from "./LanguageButton";
import { translate } from "../lib/i18n";
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
    <div className="workspace">
      <a className="skip" href="#contenido">
        {translate(" Ir al contenido ")}
      </a>
      <header className="top">
        <Brand />
        <span className="demo">{translate("Piloto · Datos simulados")}</span>
        <LanguageButton />
        <ThemeButton />
      </header>
      <div className="shell">
        <aside className="sidebar">
          <div className="sidebar-menu">
            <div className="org">
              <small>{translate(roast ? "TOSTADORA" : "PROVEEDOR")}</small>
              <strong>{translate(name)}</strong>
            </div>
            <nav aria-label={translate("Navegación principal")}>
              {translate(
                (roast
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
                )),
              )}
            </nav>
          </div>
          <div className="tools">
            <button className="quiet" onClick={s.logout}>
              {translate(" Cerrar sesión ")}
            </button>
            {translate(
              s.canReset && (
                <button className="quiet" onClick={() => setConfirm(true)}>
                  Restablecer demo
                </button>
              ),
            )}
            {translate(
              confirm && (
                <div className="reset">
                  <p>
                    ¿Volver al escenario inicial y borrar los cambios de la
                    entrevista?
                  </p>
                  <button onClick={s.reset}>Sí, restablecer</button>{" "}
                  <button
                    className="secondary"
                    onClick={() => setConfirm(false)}
                  >
                    Cancelar
                  </button>
                </div>
              ),
            )}
          </div>
        </aside>
        <main tabIndex={-1} id="contenido">
          <div role="status" className={s.notice ? "feedback" : ""}>
            {translate(s.notice)}
          </div>
          <div className="route-view" key={pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
