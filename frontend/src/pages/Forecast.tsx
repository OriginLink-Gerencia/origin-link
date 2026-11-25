import "./forecast.css";
import WeeklyTrend from "../components/WeeklyTrend";
import { useState } from "react";
import { Action, Header, Panel, Table } from "../components/UI";
import {
  after,
  dateLabel,
  forecast,
  kg,
  referenceLot,
  visibleLots,
} from "../lib/demo";
import { useDemo } from "../lib/session";

export default function Forecast() {
  const { data } = useDemo();
  const lots = visibleLots(data).filter((l) => l.available >= l.minimum);
  const [selected, setSelected] = useState<number | undefined>(undefined);
  const [showTable, setShowTable] = useState(false);
  const lot = lots.find((l) => l.id === selected);
  const reference=lot ?? referenceLot(data);
  const f = forecast(data, reference?.days ?? 7, reference?.minimum ?? 0);
  const demand = f.demand;
  const history = f.history.slice(-4);
  const projected = Array.from({ length: 4 }, (_, i) => ({
    date: after(i * 7, f.first),
    kg: f.prediction.values[i],
  }));
  const gap = lot ? Math.max(0, lot.days - f.daysStock) : 0;
  const covered = Math.min(f.stock, demand);
  const inbound = Math.min(f.incoming, demand - covered);
  return (
    <div className="forecast-page">
      <Header
        eyebrow="Planificación / 25 noviembre 2026"
        title="Pronóstico y reposición"
      >
        Demanda simulada de café verde para las próximas cuatro semanas.
      </Header>
      <div className="forecast-top">
        <section className="decision">
          <small>Necesidad neta de reposición</small>
          <h2>{history.length?kg(f.need):"Sin historial"}</h2>
          <p>
            {!history.length ? f.prediction.reason : !f.need ? (
              "La cobertura prevista alcanza para el periodo."
            ) : (
              <>
                Fecha límite sugerida <strong>{dateLabel(f.date)}</strong>
              </>
            )}
          </p>
          <dl className="decision-factors">
            <div>
              <dt>Consumo semanal</dt>
              <dd>{kg(f.mean)}</dd>
            </div>
            <div>
              <dt>Cobertura en almacén</dt>
              <dd>{f.daysStock} días</dd>
            </div>
          </dl>
          <Action to="/lotes?comparar=1">Comparar lotes disponibles →</Action>
        </section>
        <Panel title="Balance de abastecimiento">
          <div className="balance-total">
            <span>Demanda prevista</span>
            <strong>{kg(demand)}</strong>
          </div>
          <div className="coverage-bar" aria-hidden="true">
            {[covered, inbound, Math.max(0, demand - covered - inbound)].map(
              (v, i) => (
                <i
                  key={i}
                  style={{ width: (demand ? (v / demand) * 100 : 0) + "%" }}
                />
              ),
            )}
          </div>
          <dl className="balance-ledger">
            {[
              ["Existencias actuales", kg(f.stock)],
              ["Compras por recibir", kg(f.incoming)],
              ["Pendiente de cubrir", kg(f.gap)],
            ].map(([label, v]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
          <p className="forecast-note">
            El saldo descuenta las existencias y las compras con entrega
            prevista dentro de 28 días. La recomendación usa el plazo de entrega y dos semanas de cobertura.
          </p>
        </Panel>
      </div>
      <section className="panel forecast-trend">
        <header className="trend-head">
          <div>
            <h2>Consumo semanal</h2>
            <p>Kilos por semana · {f.prediction.method}</p>
          </div>
          <div
            className="view-switch"
            role="group"
            aria-label="Vista del consumo"
          >
            <button
              type="button"
              aria-pressed={!showTable}
              onClick={() => setShowTable(false)}
            >
              Gráfico
            </button>
            <button
              type="button"
              aria-pressed={showTable}
              onClick={() => setShowTable(true)}
            >
              Tabla
            </button>
          </div>
        </header>
        {showTable ? (
          <Table labels={["Semana del", "Serie", "Consumo (kg)"]}>
            {[...history, ...(history.length?projected:[])].map((w, i) => (
              <tr key={w.date}>
                <td>{dateLabel(w.date)}</td>
                <td>
                  {i < history.length ? "Historial" : "Pronóstico simulado"}
                </td>
                <td>{w.kg.toLocaleString("es-PE")}</td>
              </tr>
            ))}
          </Table>
        ) : (
          <WeeklyTrend history={history} projected={history.length ? projected : []} />
        )}
      </section>
      <Panel title="Método y evaluación">
        <p><strong>{f.prediction.method}</strong> · {f.prediction.reason}</p>
        {f.prediction.report && <Table labels={["Evaluación de esta tostadora","MAPE TCN","MAPE promedio móvil"]}>
          <tr><th>Validación · 8 semanas</th>{f.prediction.report.validation.map((v,i)=><td key={i}>{v}</td>)}</tr>
          <tr><th>Prueba · últimas 6 semanas</th>{f.prediction.report.test.map((v,i)=><td key={i}>{v}</td>)}</tr>
        </Table>}
        <details><summary>Resultados del Project Charter</summary><p>El ensayo global documentado con cuatro tostadoras sintéticas obtuvo un MAPE de 9,00 % con TCN y 12,37 % con promedio móvil a cuatro semanas. A una semana obtuvo 8,85 % y 8,86 %. La tabla muestra la evaluación del modelo local del piloto a cuatro semanas.</p></details>
      </Panel>
      <Panel title="Simular el plazo de reposición">
        <p>Referencia de cálculo: {reference ? reference.code : "Sin compras previas"} · {f.days} días de entrega · {kg(f.minimum)} de mínimo · 2 semanas de cobertura.</p>
        {lots.length ? (
          <>
            <div className="scenario">
              <label>
                Condiciones de referencia
                <select
                  value={selected??""}
                  onChange={(e) => setSelected(e.target.value?+e.target.value:undefined)}
                >
                  <option value="">Condiciones de la última compra o del piloto</option>
                  {lots.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.code} · {l.variety} · {l.days} días
                    </option>
                  ))}
                </select>
              </label>
              {lot && <dl className="scenario-data">
                <div>
                  <dt>Disponible</dt>
                  <dd>{kg(lot.available)}</dd>
                </div>
                <div>
                  <dt>Pedido mínimo</dt>
                  <dd>{kg(lot.minimum)}</dd>
                </div>
                <div>
                  <dt>Si compras hoy, llega el</dt>
                  <dd>{dateLabel(after(lot.days))}</dd>
                </div>
              </dl>}
            </div>
            {lot && <><p role="status" className="scenario-result">
              {!f.need
                ? "No necesitas reponer para cubrir la demanda estimada."
                : gap
                  ? "El plazo de " +
                    lot.days +
                    " días supera en " +
                    gap +
                    " " +
                    (gap === 1 ? "día" : "días") +
                    " la cobertura del stock actual. Revisa las entregas pendientes antes de confirmar."
                  : "El plazo de entrega cabe dentro de la cobertura actual. Puedes registrar la compra hasta el " +
                    dateLabel(f.date) +
                    "."}{" "}
              {f.need > lot.available &&
                "Este lote cubre solo una parte de la reposición."}
            </p>
            <Action secondary to={"/lotes/" + lot.id}>
              Revisar ficha de {lot.code} →
            </Action></>}
          </>
        ) : (
          <p>
            No hay lotes vinculados con cantidad suficiente para el pedido
            mínimo.
          </p>
        )}
      </Panel>
    </div>
  );
}
