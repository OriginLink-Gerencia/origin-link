import { useEffect, useState } from "react";
import { useAuth } from "../auth/useAuth";
import { getHealth } from "../lib/api";

export default function Inicio() {
  const { usuario } = useAuth();
  const [estadoApi, setEstadoApi] = useState("verificando?");
  const esProveedor = usuario?.organizacion.tipo === "PROVEEDOR";

  useEffect(() => {
    getHealth()
      .then((h) => setEstadoApi(`${h.status} (${h.environment})`))
      .catch(() => setEstadoApi("sin conexi?n"));
  }, []);

  return (
    <section>
      <h1 className="text-2xl font-semibold">
        {esProveedor ? "Panel de cooperativa" : "Panel del tostador"}
      </h1>
      <p className="mt-2 text-stone-600">
        {esProveedor
          ? "Comparte tus lotes con las empresas tostadoras vinculadas."
          : "Planifica el abastecimiento de caf? verde con tus proveedores vinculados."}
      </p>
      <p className="mt-6 text-sm text-stone-500">Estado de la API: {estadoApi}</p>
    </section>
  );
}
