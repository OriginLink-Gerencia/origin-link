import { translate } from "./lib/i18n";
import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import Forecast from "./pages/Forecast";
import { Action, Header } from "./components/UI";
import Layout from "./components/Layout";
import { usePilot } from "./lib/pilotSession";
import { SessionContext } from "./lib/session";
import { Access, Overview, Partners } from "./pages/Workspace";
import { Catalog, LotDetail, LotEditor } from "./pages/Lots";
import { Orders, Inventory } from "./pages/Operations";
export default function App() {
  const [, refreshLanguage] = useState(0);
  useEffect(() => {
    const refresh = () => refreshLanguage((n) => n + 1);
    window.addEventListener("originlink-language", refresh);
    return () => window.removeEventListener("originlink-language", refresh);
  }, []);
  const nav = useNavigate(),
    location = useLocation(),
    pilot = usePilot(nav);
  const [theme, setTheme] = useState(
    () => localStorage.getItem("ol.theme") === "dark",
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme ? "dark" : "light";
    localStorage.setItem("ol.theme", theme ? "dark" : "light");
  }, [theme]);
  useEffect(() => {
    document.title =
      (document.querySelector("h1")?.textContent || "Demo") + " · OriginLink";
    const main = document.querySelector<HTMLElement>("main");
    main?.focus({ preventScroll: true });
    const target =
      location.hash && document.getElementById(location.hash.slice(1));
    if (target) target.scrollIntoView();
    else if (main?.id === "contenido") main.scrollTop = 0;
    else window.scrollTo(0, 0);
  }, [location.pathname, location.hash, pilot.role]);
  const roast = pilot.role === "tostadora";
  const denied = (
    <>
      <Header
        eyebrow={translate("Permisos de la cuenta")}
        title={translate("Acceso restringido")}
      >
        {translate(" Esta sección requiere otro rol. ")}
      </Header>
      <Action to="/">{translate("Volver a mi panel")}</Action>
    </>
  );
  const legacyInvitation = /^\/invitacion(?:\/|$)/.test(location.pathname);
  if (legacyInvitation) return <Navigate replace to="/" />;
  return (
    <SessionContext.Provider
      value={{ ...pilot, theme, toggleTheme: () => setTheme(!theme) }}
    >
      {translate(
        !pilot.role ? (
          <Access key={location.pathname} />
        ) : (
          <Routes>
            <Route element={<Layout />}>
              <Route index element={roast ? <Overview /> : <Partners />} />
              <Route path="proveedores" element={<Partners />} />
              <Route path="lotes" element={<Catalog />} />
              <Route path="lotes/:id" element={<LotDetail />} />
              <Route
                path="lote-manual"
                element={roast ? <LotEditor /> : denied}
              />
              <Route
                path="inventario"
                element={roast ? <Inventory /> : denied}
              />
              <Route
                path="pronostico"
                element={roast ? <Forecast /> : denied}
              />
              <Route path="compras" element={roast ? <Orders /> : denied} />
              <Route path="publicar" element={roast ? denied : <LotEditor />} />
              <Route
                path="editar/:id"
                element={roast ? denied : <LotEditor />}
              />
              <Route path="*" element={<Navigate replace to="/" />} />
            </Route>
          </Routes>
        ),
      )}
    </SessionContext.Provider>
  );
}
