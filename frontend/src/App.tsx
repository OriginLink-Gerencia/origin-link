import { useEffect, useState } from "react";
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";
import Forecast from "./pages/Forecast";
import Layout from "./components/Layout";
import {usePilot} from "./lib/pilotSession";
import { SessionContext } from "./lib/session";
import { Access, Overview, Partners } from "./pages/Workspace";
import { Catalog, LotDetail, LotEditor } from "./pages/Lots";
import { Orders, Inventory } from "./pages/Operations";
export default function App() {
  const nav = useNavigate(), location=useLocation(), pilot=usePilot(nav);
  const [theme,setTheme]=useState(()=> localStorage.getItem("ol.theme")==="dark");
  useEffect(() => {
    document.documentElement.dataset.theme = theme ? "dark" : "light";
    localStorage.setItem("ol.theme", theme ? "dark" : "light");
  }, [theme]);
  useEffect(() => {
    document.title =
      (document.querySelector("h1")?.textContent || "Demo") + " · OriginLink";
    document.querySelector<HTMLElement>("main")?.focus();
    if (location.hash)
      document.getElementById(location.hash.slice(1))?.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [location.pathname, location.hash, pilot.role]);
  const roast=pilot.role==="tostadora";
  const invited=location.pathname==="/invitacion";
  return (
    <SessionContext.Provider value={{...pilot,theme,toggleTheme:()=>setTheme(!theme)}}>
      {!pilot.role || invited ? (
        <Access />
      ) : (
        <Routes>
          <Route element={<Layout />}>
            <Route index element={roast ? <Overview /> : <Partners />} />
            <Route path="proveedores" element={<Partners />} />
            <Route path="lotes" element={<Catalog />} />
            <Route path="lotes/:id" element={<LotDetail />} />
            {roast ? (
              <>
                <Route path="lote-manual" element={<LotEditor />} />
                <Route path="inventario" element={<Inventory />} />
                <Route path="pronostico" element={<Forecast />} />
                <Route path="compras" element={<Orders />} />
              </>
            ) : (
              <>
                <Route path="publicar" element={<LotEditor />} />
                <Route path="editar/:id" element={<LotEditor />} />
              </>
            )}
            <Route path="*" element={<Navigate replace to="/" />} />
          </Route>
        </Routes>
      )}
    </SessionContext.Provider>
  );
}
