import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import EnConstruccion from "./pages/EnConstruccion";
import Inicio from "./pages/Inicio";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path="proveedores" element={<EnConstruccion titulo="Proveedores" historia="épica de relaciones" />} />
        <Route path="lotes" element={<EnConstruccion titulo="Lotes" historia="épica colaborativa" />} />
        <Route path="compras" element={<EnConstruccion titulo="Compras y recepciones" historia="épica de compras" />} />
        <Route path="inventario" element={<EnConstruccion titulo="Inventario" historia="épica de inventario" />} />
        <Route path="pronostico" element={<EnConstruccion titulo="Pronóstico y recomendaciones" historia="épica de pronóstico" />} />
      </Route>
    </Routes>
  );
}
