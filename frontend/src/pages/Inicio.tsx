import { translate } from "../lib/i18n";
import { useEffect, useState } from "react";
import { getHealth } from "../lib/api";

export default function Inicio() {
  const [estadoApi, setEstadoApi] = useState("verificando…");

  useEffect(() => {
    getHealth()
      .then((h) => setEstadoApi(`${h.status} (${h.environment})`))
      .catch(() => setEstadoApi("sin conexión"));
  }, []);

  return (
    <section>
      <h1 className="text-2xl font-semibold">
        {translate("Panel del tostador")}
      </h1>
      <p className="mt-2 text-stone-600">
        {translate(
          " Planifica el abastecimiento de café verde con tus proveedores vinculados. ",
        )}
      </p>
      <p className="mt-6 text-sm text-stone-500">
        {translate("Estado de la API: ")}
        {translate(estadoApi)}
      </p>
    </section>
  );
}
