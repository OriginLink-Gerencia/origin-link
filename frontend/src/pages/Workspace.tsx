import {Link} from "react-router-dom";
import {Action, Header, Panel} from "../components/UI";
import {balance,dateLabel,kg,pending,visibleLots} from "../lib/demo";
import {summary} from "../lib/plan";
import {useDemo} from "../lib/session";
export { default as Access } from "./Access";
export { default as Partners } from "./Partners";
export function Overview() {
  const { data: d, plan, name, region } = useDemo(),
    f = summary(d, plan),
    open = d.orders.filter((o) => pending(o) > 0);
  return (
    <>
      <Header
        eyebrow={[name,region].filter(Boolean).join(" / ")}
        title="Resumen de abastecimiento"
      />
      <section className="feature">
        <div>
          <small>Plan de reposición</small>
          <h2>{f.need ? <>Reponer {kg(f.need)}</> : "Cobertura suficiente"}</h2>
          <p>
            {f.need > 0 && <>Compra sugerida para el {dateLabel(f.date)} · </>}
            Cobertura actual de {f.daysStock} días
          </p>
          <Action to="/pronostico">Revisar recomendación →</Action>
        </div>
        <div className="supply-breakdown">
          <h3>Balance a cuatro semanas</h3>
          <dl>
            <div><dt>Consumo previsto</dt><dd>{kg(f.mean * 4)}</dd></div>
            <div><dt>En inventario</dt><dd>{kg(f.stock)}</dd></div>
            <div><dt>Por recibir en el periodo</dt><dd>{kg(f.incoming)}</dd></div>
            <div className="net-need"><dt>Pendiente de cubrir</dt><dd>{kg(f.gap)}</dd></div>
          </dl>
        </div>
      </section>
      <div className="metrics">
        {[
          ["Existencias", kg(balance(d)), "/inventario"],
          ["Compras pendientes", String(open.length), "/compras"],
          ["Lotes vinculados", String(visibleLots(d).length), "/lotes"],
        ].map(([label, v, to]) => (
          <Link to={to} key={label}>
            <small>{label}</small>
            <strong>{v}</strong>
            <span>Ver detalle →</span>
          </Link>
        ))}
      </div>
      <Panel title="Requiere atención">
        {(f.low || (f.need > 0 && f.daysStock <= f.days + 7)) && (
          <Link className="item" to="/pronostico">
            <strong>
              {f.low ? "Alerta de stock bajo" : "Próxima reposición"}
            </strong>
            <span>{(f.mean ? f.stock/f.mean : 0).toLocaleString("es-PE",{maximumFractionDigits:1})} semanas de cobertura · Revisar →</span>
          </Link>
        )}
        {open.map((o) => (
          <Link className="item" to={"/compras#pedido-" + o.id} key={o.id}>
            <strong>
              Compra #{o.id} · {kg(pending(o))} por recibir
            </strong>
            <span>Entrega {dateLabel(o.due)} →</span>
          </Link>
        ))}
        {!open.length && !f.low && (!f.need || f.daysStock > f.days + 7) && <p>Sin alertas pendientes.</p>}
      </Panel>
    </>
  );
}

