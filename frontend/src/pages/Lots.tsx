import { translate } from "../lib/i18n";
import { performance } from "../lib/performance";
import DateField from "../components/DateField";
import NumberField from "../components/NumberField";
import { values } from "../lib/form";
import { useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { Action, Header, Panel, Table } from "../components/UI";
import {
  after,
  kg,
  money,
  ownLots,
  TODAY,
  visibleLots,
} from "../lib/demo";
import type { Data, Lot } from "../lib/demo";
import { useDemo } from "../lib/session";
const processes = ["Lavado", "Honey", "Natural", "Anaeróbico", "Otro"];
function specs(d: Data, l: Lot) {
  const supplier = d.suppliers.find((p) => p.id === l.supplier);
  const stats = performance(
    d.orders.filter(
      (o) => d.lots.find((lot) => lot.id === o.lot)?.supplier === l.supplier,
    ),
  );
  return {
    Proveedor: supplier?.name,
    "Cumplimiento de cantidad": stats?.weight ?? "Sin entregas",
    "Entregas a tiempo": stats?.onTime ?? "Sin entregas",
    "Última actualización": l.updated ?? TODAY,
    Origen: l.region ?? d.suppliers.find((p) => p.id === l.supplier)?.region,
    Finca: l.farm,
    Variedad: l.variety,
    Proceso: l.process,
    Cosecha: l.harvest,
    Altitud: l.altitude + " m s. n. m.",
    "Precio por kg": money(l.price),
    Disponible: kg(l.available),
    "Compra mínima": kg(l.minimum),
    "Plazo de entrega": l.days + " días",
  };
}
export function Catalog() {
  const s = useDemo(),
    d = s.data,
    roast = s.role === "tostadora",
    [params] = useSearchParams(),
    lots = roast ? visibleLots(d) : ownLots(d, s.supplier);
  const [query, Q] = useState(""),
    [supplier, S] = useState(params.get("proveedor") ?? ""),
    [process, P] = useState(""),
    [available, A] = useState(false),
    [ids, I] = useState<number[]>(
      params.has("comparar")
        ? lots
            .filter((l) => l.available >= l.minimum)
            .slice(0, 2)
            .map((l) => l.id)
        : [],
    );
  const rows = lots.filter(
    (l) =>
      (!supplier || l.supplier === +supplier) &&
      (!process || l.process === process) &&
      (!available || l.available >= l.minimum) &&
      [
        l.code,
        l.variety,
        l.farm,
        specs(d, l).Origen,
        d.suppliers.find((p) => p.id === l.supplier)?.name,
      ]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query.toLocaleLowerCase().trim()),
  );
  const [showComparison, setShowComparison] = useState(params.has("comparar"));
  const compare = lots.filter((l) => ids.includes(l.id));
  const filtered = Boolean(query || supplier || process || available);
  function clearFilters() {
    Q("");
    S("");
    P("");
    A(false);
  }
  return (
    <>
      <Header
        eyebrow={
          roast
            ? "Abastecimiento / Catálogo privado"
            : "Portal de la cooperativa"
        }
        title={roast ? "Lotes de café verde" : "Mis lotes"}
      >
        {translate(
          roast
            ? "Consulta el origen y las condiciones de tus proveedores vinculados."
            : "Administra la disponibilidad que ven tus tostadoras vinculadas.",
        )}
      </Header>
      {translate(
        roast && d.suppliers.some((p) => !p.linked) && (
          <Action secondary to="/lote-manual">
            Registrar lote manual
          </Action>
        ),
      )}
      {translate(!roast && <Action to="/publicar">Publicar lote</Action>)}
      <div
        className="filters"
        role="group"
        aria-label={translate("Filtros del catálogo")}
      >
        <label>
          {translate(" Buscar ")}
          <input
            type="search"
            value={query}
            placeholder={translate("Código, finca o variedad")}
            onChange={(e) => Q(e.target.value)}
          />
        </label>
        {translate(
          roast && (
            <label>
              Proveedor
              <select value={supplier} onChange={(e) => S(e.target.value)}>
                <option value="">Todos</option>
                {d.suppliers
                  .filter(
                    (p) => p.linked || lots.some((l) => l.supplier === p.id),
                  )
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
              </select>
            </label>
          ),
        )}
        <label>
          {translate(" Proceso ")}
          <select value={process} onChange={(e) => P(e.target.value)}>
            <option value="">{translate("Todos")}</option>
            {translate(
              processes.map((p) => (
                <option value={p} key={p}>
                  {p}
                </option>
              )),
            )}
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={available}
            onChange={(e) => A(e.target.checked)}
          />
          {translate(" ")}
          {translate(" Con disponibilidad ")}
        </label>
      </div>
      <div className="catalog-count">
        <span aria-live="polite">
          {translate(rows.length)}
          {translate(" ")}
          {translate(
            rows.length === 1 ? "lote en el catálogo" : "lotes en el catálogo",
          )}
        </span>
        {translate(
          filtered && (
            <button className="text-action" onClick={clearFilters}>
              Limpiar filtros
            </button>
          ),
        )}
      </div>
      <div className="cards">
        {translate(
          rows.map((l) => (
            <article
              className="lotcard"
              data-selected={roast && ids.includes(l.id)}
              key={l.id}
            >
              <header className="lot-head">
                <small>
                  {specs(d, l).Origen} · {l.code}
                </small>
                <span className="process-tag">{l.process}</span>
              </header>
              <h2>{l.variety}</h2>
              <p>
                {specs(d, l).Proveedor} · {l.altitude} m s. n. m.
              </p>
              <p>{l.farm}</p>
              {l.owner && <small>Registrado por el tostador</small>}
              <dl className="lot-terms">
                <div>
                  <dt>Precio por kg</dt>
                  <dd>{money(l.price)}</dd>
                </div>
                <div>
                  <dt>Disponible</dt>
                  <dd>{l.available ? kg(l.available) : "Agotado"}</dd>
                </div>
              </dl>
              <footer className="lot-actions">
                <Action secondary to={"/lotes/" + l.id}>
                  Ver ficha
                </Action>
                {roast && (
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={ids.includes(l.id)}
                      disabled={ids.length >= 4 && !ids.includes(l.id)}
                      onChange={(e) =>
                        I(
                          e.target.checked
                            ? [...ids, l.id]
                            : ids.filter((i) => i !== l.id),
                        )
                      }
                    />{" "}
                    Comparar<span className="sr-only"> {l.code}</span>
                  </label>
                )}
              </footer>
            </article>
          )),
        )}
      </div>
      {translate(
        !rows.length && (
          <p className="empty-state">
            {filtered
              ? "Ningún lote coincide con estos filtros."
              : "Aún no hay lotes publicados."}
          </p>
        ),
      )}
      {translate(
        roast && (
          <Panel title="Comparación de lotes">
            <button
              disabled={compare.length < 2}
              onClick={() => setShowComparison(true)}
            >
              Comparar lotes ({compare.length}/4)
            </button>
            {compare.length < 2 || !showComparison ? (
              <p>
                Selecciona entre dos y cuatro lotes para comparar sus
                condiciones.
              </p>
            ) : (
              <Table labels={["Característica", ...compare.map((l) => l.code)]}>
                {Object.keys(specs(d, compare[0])).map((k, i) => (
                  <tr key={k}>
                    <th>{k}</th>
                    {compare.map((l) => (
                      <td key={l.id}>{Object.values(specs(d, l))[i]}</td>
                    ))}
                  </tr>
                ))}
                <tr>
                  <th>Ficha y compra</th>
                  {compare.map((l) => (
                    <td key={l.id}>
                      <Link to={"/lotes/" + l.id}>Elegir {l.code}</Link>
                    </td>
                  ))}
                </tr>
              </Table>
            )}
          </Panel>
        ),
      )}
    </>
  );
}
export function LotDetail() {
  const s = useDemo(),
    d = s.data,
    { id } = useParams(),
    nav = useNavigate(),
    roast = s.role === "tostadora";
  const l = (roast ? visibleLots(d) : ownLots(d, s.supplier)).find(
    (l) => l.id === Number(id),
  );
  if (!l)
    return (
      <Panel title={translate("Lote no disponible")}>
        <Action to="/lotes">{translate("Volver a lotes")}</Action>
      </Panel>
    );
  return (
    <>
      <Link to="/lotes">{translate("← Catálogo")}</Link>
      <Header
        eyebrow={l.code + " / " + specs(d, l).Origen}
        title={l.variety + " · " + l.process}
      >
        {translate(d.suppliers.find((p) => p.id === l.supplier)?.name)}
      </Header>
      <Panel title={translate("Ficha de origen")}>
        <dl className="specs">
          {translate(
            Object.entries(specs(d, l)).map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            )),
          )}
        </dl>
        <h3>{translate("Muestra y evaluación declarada")}</h3>
        <p>{translate(l.notes || "Sin evaluación registrada.")}</p>
      </Panel>
      {translate(
        roast ? (
          <Panel title="Registrar compra acordada">
            {l.available < l.minimum ? (
              <p>La disponibilidad es inferior al pedido mínimo.</p>
            ) : (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const v = values(e.currentTarget);
                  if (await s.buy(l.id, +v.kg, +v.price, v.due)) nav("/compras");
                }}
              >
                <div className="fields">
                  <NumberField
                    label="Cantidad acordada (kg)"
                    required
                    name="kg"

                    min={l.minimum}
                    step=".01"
                    defaultValue={l.minimum}
                  />
                  <NumberField
                    label="Precio acordado (S/ por kg)"
                    required
                    name="price"

                    min=".01"
                    step=".01"
                    defaultValue={l.price}
                  />
                  <DateField
                    label="Entrega acordada"
                    name="due"
                    min={TODAY}
                    defaultValue={after(l.days)}
                  />
                </div>
                <p>Disponible para esta compra: {kg(l.available)}.</p>
                <button>Confirmar compra</button>
              </form>
            )}
          </Panel>
        ) : (
          <Action to={"/editar/" + l.id}>Editar lote y disponibilidad</Action>
        ),
      )}
    </>
  );
}
export function LotEditor() {
  const s = useDemo(),
    { id } = useParams(),
    nav = useNavigate(),
    manual = s.role === "tostadora",
    options = s.data.suppliers.filter((p) => !p.linked),
    [selected, setSelected] = useState(options[0]?.id),
    supplier = s.data.suppliers.find(
      (p) => p.id === (manual ? selected : s.supplier),
    );
  const existing = ownLots(s.data, s.supplier).find((l) => l.id === Number(id));
  if (!supplier || (!manual && !supplier.linked) || (id && !existing))
    return (
      <Panel title={translate("Publicación no disponible")}>
        <Action to="/">{translate("Revisar vínculos")}</Action>
      </Panel>
    );
  const l = existing;
  return (
    <>
      <Header
        eyebrow={supplier.name}
        title={
          manual
            ? "Registrar lote manual"
            : l
              ? "Editar " + l.code
              : "Publicar lote"
        }
      />
      <form
        className="panel"
        key={id ?? "nuevo"}
        onSubmit={async (e) => {
          e.preventDefault();
          const v = values(e.currentTarget);
          const lot: Lot = {
            id: l?.id ?? 0,
            supplier: supplier.id,
            owner: manual ? s.supplier : undefined,
            documents: l?.documents,
            region: v.region.trim(),
            code: v.code.trim(),
            farm: v.farm.trim(),
            variety: v.variety.trim(),
            process: v.process,
            harvest: +v.harvest,
            altitude: +v.altitude,
            price: +v.price,
            available: +v.available,
            minimum: +v.minimum,
            days: +v.days,
            notes: v.notes.trim(),
          };
          // Un lote ya publicado solo cambia sus condiciones de venta; el resto de la ficha queda como se registró.
          const saved: Lot = l
            ? { ...l, price: lot.price, available: lot.available, minimum: lot.minimum, days: lot.days }
            : lot;
          if (await s.saveLot(saved, manual)) nav("/lotes");
        }}
      >
        {translate(
          manual && (
            <label>
              Proveedor sin vincular
              <select
                value={selected}
                onChange={(e) => setSelected(+e.target.value)}
              >
                {options.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
          ),
        )}
        <div className="fields">
          <label>
            {translate(" Región de origen ")}
            <input
              name="region"
              required
              key={supplier.id}
              defaultValue={l?.region ?? supplier.region}
              readOnly={Boolean(l)}
            />
          </label>
          {translate(
            (
              [
                ["code", "Código"],
                ["farm", "Finca y localidad"],
                ["variety", "Variedad"],
              ] as const
            ).map(([k, n]) => (
              <label key={k}>
                {n}
                <input
                  name={k}
                  required
                  defaultValue={l?.[k]}
                  readOnly={Boolean(l)}
                />
              </label>
            )),
          )}
          <label>
            {translate(" Proceso ")}
            <select
              name="process"
              defaultValue={l?.process}
              disabled={Boolean(l)}
            >
              {translate(
                processes.map((p) => (
                  <option value={p} key={p}>
                    {p}
                  </option>
                )),
              )}
            </select>
          </label>
          {translate(
            (
              [
                ["harvest", "Año de cosecha", 2000, 2026, 1],
                ["altitude", "Altitud (m s. n. m.)", 1, 4500, 1],
                ["price", "Precio (S/ por kg)", 0.01, 9999, 0.01],
                [
                  "available",
                  "Disponibilidad (kg)",
                  l ? 0 : 0.01,
                  999999,
                  0.01,
                ],
                ["minimum", "Pedido mínimo (kg)", 0.01, 999999, 0.01],
                ["days", "Plazo de entrega (días)", 1, 365, 1],
              ] as const
            ).map(([k, label, min, max, step]) => (
              <NumberField
                key={k}
                label={label}
                name={k}
                required
                readOnly={Boolean(l) && (k === "harvest" || k === "altitude")}
                min={min}
                max={max}
                step={step}
                defaultValue={l?.[k] ?? (k === "harvest" ? 2026 : undefined)}
              />
            )),
          )}
        </div>
        <label>
          {translate(" Ficha de muestra o evaluación ")}
          <textarea name="notes" defaultValue={l?.notes} />
        </label>
        {l && (
          <p>
            {translate(
              "Para cambiar el código, la finca, la variedad u otros datos de origen, publica un lote nuevo. Aquí puedes ajustar precio, disponibilidad, pedido mínimo y plazo.",
            )}
          </p>
        )}
        <button>
          {translate(
            manual
              ? "Guardar lote privado"
              : l
                ? "Guardar cambios"
                : "Publicar para tostadoras vinculadas",
          )}
        </button>
      </form>
    </>
  );
}
