import { translate } from "../lib/i18n";
import { readConsumption } from "../lib/consumption";
import NumberField from "../components/NumberField";
import { values } from "../lib/form";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Header, Panel, Table } from "../components/UI";
import {
  balance,
  dateLabel,
  kg,
  money,
  move,
  pending,
  receive,
  received,
  visibleLots,
} from "../lib/demo";
import type { Movement } from "../lib/demo";
import { useDemo } from "../lib/session";
export function Orders() {
  const s = useDemo(),
    d = s.data,
    [filter, F] = useState("Todas"),
    [provider, setProvider] = useState(
      new URLSearchParams(useLocation().search).get("proveedor") ?? "",
    );

  const rows = d.orders
    .filter(
      (o) =>
        !provider || d.lots.find((l) => l.id === o.lot)?.supplier === +provider,
    )
    .filter(
      (o) =>
        filter === "Todas" ||
        (filter === "Pendientes" ? pending(o) > 0 : pending(o) === 0),
    )
    .sort((a, b) => b.id - a.id);
  return (
    <>
      <Header
        eyebrow={translate("Abastecimiento / Recepciones")}
        title={translate("Compras y entregas")}
      />
      <div className="fields">
        <label>
          {translate(" Proveedor ")}
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="">{translate("Todos")}</option>
            {translate(
              d.suppliers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              )),
            )}
          </select>
        </label>
        <label>
          {translate(" Mostrar compras ")}
          <select value={filter} onChange={(e) => F(e.target.value)}>
            {translate(
              ["Todas", "Pendientes", "Recibidas"].map((f) => (
                <option value={f} key={f}>
                  {f}
                </option>
              )),
            )}
          </select>
        </label>
      </div>
      {translate(!rows.length && <p>No hay compras con este estado.</p>)}
      {translate(
        rows.map((o) => {
          const l = d.lots.find((l) => l.id === o.lot)!;
          const remain = pending(o);
          return (
            <article id={"pedido-" + o.id} key={o.id} className="panel">
              <div className="item">
                <div>
                  <small>
                    Compra #{o.id} · {dateLabel(o.date)}
                  </small>
                  <h2>
                    <Link to={"/lotes/" + l.id}>
                      {l.code} · {l.variety}
                    </Link>
                  </h2>
                </div>
                <span className="tag">
                  {remain === 0
                    ? "Recibida"
                    : received(o) > 0
                      ? "Recepción parcial"
                      : "Pendiente de recepción"}
                </span>
              </div>
              <p>
                {d.suppliers.find((p) => p.id === l.supplier)?.name} · Entrega
                acordada {dateLabel(o.due)}
              </p>
              <dl className="specs">
                {[
                  ["Acordado", kg(o.kg)],
                  ["Precio por kg", money(o.price)],
                  ["Importe", money(o.kg * o.price)],
                  ["Recibido", kg(received(o))],
                  ["Saldo pendiente", kg(remain)],
                  [
                    "Diferencia de peso",
                    o.receipts.length
                      ? (received(o) > o.kg ? "+" : "") +
                        kg(Math.round((received(o) - o.kg) * 100) / 100)
                      : "Sin recepción",
                  ],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
              {o.receipts.map((r, i) => (
                <p key={i}>
                  Recepción {i + 1} · {dateLabel(r.date)} · {kg(r.kg)}
                  {r.note ? " · " + r.note : ""}
                </p>
              ))}
              {remain > 0 && (
                <details>
                  <summary>Registrar recepción de compra #{o.id}</summary>
                  <form
                    key={remain}
                    onSubmit={(e) => {
                      e.preventDefault();
                      const v = values(e.currentTarget);
                      s.update(
                        (d) =>
                          receive(
                            d,
                            o.id,
                            +v.amount,
                            v.note,
                            v.mode === "final",
                          ),
                        "Recepción guardada. Los kilos recibidos ya están en inventario.",
                      );
                    }}
                  >
                    <div className="fields">
                      <NumberField
                        label="Peso recibido (kg)"
                        name="amount"

                        required
                        step=".01"
                        min=".01"
                        defaultValue={remain}
                      />
                      <label>
                        Tipo de recepción
                        <select name="mode">
                          <option value="final">
                            Cerrar entrega con el peso real
                          </option>
                          <option value="partial">Recepción parcial</option>
                        </select>
                      </label>
                      <label>
                        Observaciones de entrega
                        <input
                          name="note"
                          placeholder="Diferencia de peso, condición de la muestra…"
                        />
                      </label>
                    </div>
                    <button>Confirmar recepción</button>
                  </form>
                </details>
              )}{" "}
              <Link to={"/inventario?lote=" + l.id}>
                Rastrear en inventario →
              </Link>
            </article>
          );
        }),
      )}
    </>
  );
}

export function Inventory() {
  const s = useDemo(),
    d = s.data,
    lots = visibleLots(d),
    { search } = useLocation();
  const [filter, F] = useState(new URLSearchParams(search).get("lote") ?? ""),
    [kind, K] = useState<Exclude<Movement["kind"], "Entrada">>("Consumo"),
    [error, E] = useState("");
  const rows = d.moves
    .filter((m) => !filter || m.lot === +filter)
    .slice()
    .reverse();
  return (
    <>
      <Header
        eyebrow={translate("Operación / Café verde")}
        title={translate("Inventario y trazabilidad")}
      >
        {translate(" Existencias totales: ")}
        {translate(kg(balance(d)))}
        {translate(". ")}
      </Header>
      <Panel title={translate("Existencias por lote")}>
        {translate(
          !lots.some((l) => balance(d, l.id) > 0) && (
            <p>
              Aún no hay existencias. Registra la recepción de una compra para
              ingresar café.
            </p>
          ),
        )}
        <Table labels={["Lote", "Origen", "Saldo", "Trazabilidad"]}>
          {translate(
            lots
              .filter((l) => balance(d, l.id) > 0)
              .map((l) => (
                <tr key={l.id}>
                  <td>
                    <Link to={"/lotes/" + l.id}>
                      {l.code} · {l.variety}
                    </Link>
                  </td>
                  <td>{l.farm}</td>
                  <td>{kg(balance(d, l.id))}</td>
                  <td>
                    <button className="quiet" onClick={() => F(String(l.id))}>
                      Ver movimientos de {l.code}
                    </button>
                  </td>
                </tr>
              )),
          )}
        </Table>
      </Panel>
      <Panel title={translate("Registrar movimiento")}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const form = e.currentTarget,
              v = values(form);
            if (
              s.update(
                (d) => move(d, +v.lot, kind, +v.amount, v.note),
                "Movimiento guardado. Saldo actualizado.",
              )
            ) {
              form.reset();
              K("Consumo");
              F(v.lot);
            }
          }}
        >
          <div className="fields">
            <label>
              {translate(" Lote ")}
              <select name="lot" required>
                {translate(
                  lots.map((l) => (
                    <option value={l.id} key={l.id}>
                      {l.code} · {l.variety}
                    </option>
                  )),
                )}
              </select>
            </label>
            <label>
              {translate(" Tipo de movimiento ")}
              <select
                value={kind}
                onChange={(e) => K(e.target.value as typeof kind)}
              >
                {translate(
                  ["Consumo", "Merma", "Ajuste"].map((k) => (
                    <option value={k} key={k}>
                      {k}
                    </option>
                  )),
                )}
              </select>
            </label>
            <NumberField
              label={
                kind === "Ajuste" ? "Variación con signo (kg)" : "Cantidad (kg)"
              }
              step=".01"
              min={kind === "Ajuste" ? undefined : 0.01}
              required
              name="amount"
            />
            <label>
              {translate(" Motivo ")}
              {translate(kind === "Ajuste" ? "(obligatorio)" : "(opcional)")}
              <input required={kind === "Ajuste"} name="note" />
            </label>
          </div>
          <button>{translate("Guardar movimiento")}</button>
        </form>
      </Panel>
      <Panel title={translate("Historial de movimientos")}>
        <label className="short">
          {translate(" Filtrar por lote ")}
          <select value={filter} onChange={(e) => F(e.target.value)}>
            <option value="">{translate("Todos los lotes")}</option>
            {translate(
              lots.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.code}
                </option>
              )),
            )}
          </select>
        </label>
        {translate(
          !rows.length ? (
            <p>Este lote todavía no tiene movimientos.</p>
          ) : (
            <Table
              labels={[
                "Fecha",
                "Lote",
                "Movimiento",
                "Cantidad",
                "Origen del movimiento",
              ]}
            >
              {rows.map((m) => (
                <tr key={m.id}>
                  <td>{dateLabel(m.date)}</td>
                  <td>{d.lots.find((l) => l.id === m.lot)?.code}</td>
                  <td>{m.kind}</td>
                  <td>{kg(m.kg)}</td>
                  <td>
                    {m.order && (
                      <Link to={"/compras#pedido-" + m.order}>
                        Compra #{m.order} ·{" "}
                      </Link>
                    )}
                    {m.note || "Registro manual"}
                  </td>
                </tr>
              ))}
            </Table>
          ),
        )}
      </Panel>
      <details className="panel">
        <summary>{translate("Importar historial de consumo")}</summary>
        <p>
          {translate(
            " Elige un CSV o Excel (.xlsx) con las columnas fecha y kg_consumidos. Usa fechas AAAA-MM-DD. Los consumos se suman por semana y reemplazan el total previo de esa semana. ",
          )}
        </p>
        <label>
          {translate(" Archivo de consumo ")}
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={async (e) => {
              const input = e.target,
                file = input.files?.[0];
              if (!file) return;
              try {
                const imported = await readConsumption(file);
                s.update(
                  (d) => {
                    const weeks = new Map(d.history.map((w) => [w.date, w]));
                    imported.forEach((w) => weeks.set(w.date, w));
                    return { ...d, history: [...weeks.values()] };
                  },
                  imported.length === 1
                    ? "1 semana importada."
                    : imported.length + " semanas importadas.",
                );
                E("");
              } catch (ex) {
                E((ex as Error).message);
              }
              input.value = "";
            }}
          />
        </label>
        {translate(error && <p role="alert">{error}</p>)}
      </details>
    </>
  );
}
