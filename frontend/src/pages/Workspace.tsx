import { locale, languageTags } from "../lib/i18n";
import { translate } from "../lib/i18n";
import { Link } from "react-router-dom";
import { Action, Header, Panel } from "../components/UI";
import {
  balance,
  dateLabel,
  forecast,
  kg,
  pending,
  visibleLots,
} from "../lib/demo";
import { useDemo } from "../lib/session";
export { default as Access } from "./Access";
export { default as Partners } from "./Partners";
export function Overview() {
  const { data: d, name, region } = useDemo(),
    f = forecast(d),
    open = d.orders.filter((o) => pending(o) > 0);
  return (
    <>
      <Header
        eyebrow={[name, region].filter(Boolean).join(" / ")}
        title={translate("Resumen de abastecimiento")}
      />
      <section className="feature">
        <div>
          <small>{translate("Plan de reposición")}</small>
          <h2>
            {translate(
              !f.history.length ? (
                "Sin historial de consumo"
              ) : f.need ? (
                <>Reponer {kg(f.need)}</>
              ) : (
                "Cobertura suficiente"
              ),
            )}
          </h2>
          <p>
            {translate(
              f.need > 0 && <>Compra sugerida para el {dateLabel(f.date)} · </>,
            )}
            {translate(
              f.history.length
                ? "Cobertura actual de " + f.daysStock + " días"
                : "Importa el consumo semanal para calcular la cobertura.",
            )}
          </p>
          <Action to="/pronostico">
            {translate("Revisar recomendación →")}
          </Action>
        </div>
        <div className="supply-breakdown">
          <h3>{translate("Balance a cuatro semanas")}</h3>
          <dl>
            <div>
              <dt>{translate("Consumo previsto")}</dt>
              <dd>{translate(kg(f.mean * 4))}</dd>
            </div>
            <div>
              <dt>{translate("En inventario")}</dt>
              <dd>{translate(kg(f.stock))}</dd>
            </div>
            <div>
              <dt>{translate("Por recibir en el periodo")}</dt>
              <dd>{translate(kg(f.incoming))}</dd>
            </div>
            <div className="net-need">
              <dt>{translate("Pendiente de cubrir")}</dt>
              <dd>{translate(kg(f.gap))}</dd>
            </div>
          </dl>
        </div>
      </section>
      <div className="metrics">
        {translate(
          [
            ["Existencias", kg(balance(d)), "/inventario"],
            ["Compras pendientes", String(open.length), "/compras"],
            ["Lotes en catálogo", String(visibleLots(d).length), "/lotes"],
          ].map(([label, v, to]) => (
            <Link to={to} key={label}>
              <small>{label}</small>
              <strong>{v}</strong>
              <span>Ver detalle →</span>
            </Link>
          )),
        )}
      </div>
      <Panel title={translate("Requiere atención")}>
        {translate(
          (f.low || (f.need > 0 && f.daysStock <= f.days + 7)) && (
            <Link className="item" to="/pronostico">
              <strong>
                {f.low ? "Alerta de stock bajo" : "Próxima reposición"}
              </strong>
              <span>
                {(f.mean ? f.stock / f.mean : 0).toLocaleString(
                  languageTags[locale()],
                  {
                    maximumFractionDigits: 1,
                  },
                )}{" "}
                semanas de cobertura · Revisar →
              </span>
            </Link>
          ),
        )}
        {translate(
          open.map((o) => (
            <Link className="item" to={"/compras#pedido-" + o.id} key={o.id}>
              <strong>
                Compra #{o.id} · {kg(pending(o))} por recibir
              </strong>
              <span>Entrega {dateLabel(o.due)} →</span>
            </Link>
          )),
        )}
        {translate(
          !open.length && !f.low && (!f.need || f.daysStock > f.days + 7) && (
            <p>Sin alertas pendientes.</p>
          ),
        )}
      </Panel>
    </>
  );
}
