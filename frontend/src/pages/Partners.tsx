import { locale, languageTags, translate } from "../lib/i18n";
import InvitationEntry from "../components/InvitationEntry";
import { invitationPath } from "../lib/invitationUrl";
import { performance } from "../lib/performance";
import { useState } from "react";
import { Action, Header, Panel, Table } from "../components/UI";
import { dateLabel, kg, pending, received, type Supplier } from "../lib/demo";
import { createInvitation } from "../lib/workspaces";
import { values } from "../lib/form";
import { useDemo } from "../lib/session";

function DirectoryForm({ entry }: { entry?: Supplier }) {
  const s = useDemo();
  return (
    <details>
      <summary>
        {translate(entry ? "Editar contacto" : "Registrar proveedor")}
      </summary>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget,
            v = values(form);
          if (
            s.saveSupplier({
              ...entry,
              id: entry?.id ?? 0,
              linked: entry?.linked ?? false,
              invited: entry?.invited ?? false,
              name: v.name.trim(),
              region: v.region.trim(),
              contact: v.contact.trim(),
              phone: v.phone.trim(),
              email: v.email.trim().toLowerCase(),
            })
          ) {
            form.closest("details")?.removeAttribute("open");
            if (!entry) form.reset();
          }
        }}
      >
        <div className="fields">
          {translate(
            (
              [
                ["name", "Nombre del proveedor"],
                ["region", "Región de origen"],
                ["contact", "Persona de contacto"],
                ["email", "Correo de contacto"],
                ["phone", "Teléfono"],
              ] as const
            ).map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  name={key}
                  defaultValue={entry?.[key]}
                  required={key === "name"}
                  pattern={key === "name" ? ".*\\S.*" : undefined}
                  type={
                    key === "email" ? "email" : key === "phone" ? "tel" : "text"
                  }
                  readOnly={
                    key === "email" &&
                    Boolean(
                      entry?.linked ||
                      (entry?.invited && (entry.expires ?? 0) > Date.now()),
                    )
                  }
                />
              </label>
            )),
          )}
        </div>
        <button>{translate("Guardar proveedor")}</button>
      </form>
    </details>
  );
}
function DirectoryCard({ p }: { p: Supplier }) {
  const s = useDemo(),
    [copy, setCopy] = useState(""),
    active = p.invited && (p.expires ?? 0) > Date.now();
  const url = window.location.origin + invitationPath(p.token, locale());
  const orders = s.data.orders.filter(
      (o) => s.data.lots.find((l) => l.id === o.lot)?.supplier === p.id,
    ),
    stats = performance(orders);
  return (
    <article className="network-card">
      <header>
        <div>
          <small>{translate(p.region)}</small>
          <h3>{translate(p.name)}</h3>
        </div>
        <span className="tag">
          {translate(
            p.linked ? "Vinculado" : active ? "Invitado" : "Sin vincular",
          )}
        </span>
      </header>
      {translate(
        (p.contact || p.email || p.phone) && (
          <p>{[p.contact, p.email, p.phone].filter(Boolean).join(" · ")}</p>
        ),
      )}
      {translate(
        stats ? (
          <p>
            {stats.weight} de kilos recibidos · {stats.onTime} de entregas a
            tiempo · {stats.count} compras recibidas
          </p>
        ) : (
          <p>Sin entregas completadas para calcular el cumplimiento.</p>
        ),
      )}
      <div className="network-actions">
        {translate(
          p.linked ? (
            <Action secondary to={"/lotes?proveedor=" + p.id}>
              Ver lotes
            </Action>
          ) : !active ? (
            <button
              onClick={() =>
                s.update(
                  (d) => ({
                    ...d,
                    suppliers: d.suppliers.map((entry) =>
                      entry.id === p.id ? createInvitation(entry) : entry,
                    ),
                  }),
                  "Invitación creada. Comparte el enlace con el proveedor.",
                )
              }
            >
              Invitar proveedor
            </button>
          ) : null,
        )}
        <Action secondary to={"/compras?proveedor=" + p.id}>
          {translate(" Historial de compras ")}
        </Action>
      </div>
      {translate(
        active && (
          <div className="invite-link">
            <label>
              Enlace vigente hasta el{" "}
              {new Date(p.expires!).toLocaleDateString(languageTags[locale()])}
              <input readOnly value={url} onFocus={(e) => e.target.select()} />
            </label>
            <button
              className="secondary"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(url);
                  setCopy("Enlace copiado.");
                } catch {
                  setCopy("Selecciona el enlace para copiarlo.");
                }
              }}
            >
              Copiar enlace
            </button>
            <span role="status">{copy}</span>
          </div>
        ),
      )}
      <DirectoryForm entry={p} />
    </article>
  );
}
export default function Partners() {
  const s = useDemo();
  if (s.role === "tostadora")
    return (
      <>
        <Header eyebrow={s.name} title={translate("Proveedores")}>
          {translate(
            " Tu directorio de abastecimiento y el cumplimiento de las entregas. ",
          )}
        </Header>
        <section className="panel">
          <DirectoryForm />
        </section>
        <Panel title={translate("Directorio privado")}>
          {translate(
            !s.data.suppliers.length ? (
              <p>Aún no has registrado proveedores.</p>
            ) : (
              <div className="network-list">
                {s.data.suppliers.map((p) => (
                  <DirectoryCard key={p.id} p={p} />
                ))}
              </div>
            ),
          )}
        </Panel>
      </>
    );
  const active = s.relations.filter((r) => r.entry.linked),
    invitations = s.relations.filter((r) => !r.entry.linked);
  return (
    <>
      <Header eyebrow={s.name} title={translate("Vínculos y pedidos")}>
        {translate(
          " Consulta las tostadoras que reciben tu café y sigue sus pedidos. ",
        )}
      </Header>
      <Panel title={"Tostadoras vinculadas (" + active.length + ")"}>
        <div className="network-list">
          {translate(
            active.map((r) => (
              <article className="network-card" key={r.id}>
                <header>
                  <div>
                    <small>{r.region}</small>
                    <h3>{r.name}</h3>
                  </div>
                  <span className="tag">Vínculo activo</span>
                </header>
                <p>
                  {s.data.orders.filter((o) => o.roasterId === r.id).length}{" "}
                  pedidos registrados
                </p>
              </article>
            )),
          )}
        </div>
        {translate(
          !active.length && <p>Aún no tienes tostadoras vinculadas.</p>,
        )}
      </Panel>
      <Panel title={translate("Invitaciones pendientes")}>
        {!invitations.length && (
          <p>{translate("No tienes invitaciones pendientes.")}</p>
        )}
        {invitations.map((r) => (
          <div className="item" key={r.entry.token}>
            <div>
              <strong>{r.name}</strong>
              <small>
                {translate("Enlace vigente hasta el")}{" "}
                {new Date(r.entry.expires!).toLocaleDateString(
                  languageTags[locale()],
                )}
              </small>
            </div>
            <button onClick={() => s.acceptLink(r.entry.token!)}>
              {translate("Aceptar invitación")}
            </button>
          </div>
        ))}
        <InvitationEntry />
      </Panel>
      <Panel title={translate("Pedidos de mis tostadoras")}>
        {translate(
          !s.data.orders.length ? (
            <p>Aún no hay pedidos de tus lotes.</p>
          ) : (
            <Table
              labels={[
                "Tostadora",
                "Lote",
                "Compra",
                "Entrega acordada",
                "Acordado",
                "Recibido",
                "Por entregar",
              ]}
            >
              {s.data.orders.map((o) => (
                <tr key={o.id}>
                  <td>{o.roaster}</td>
                  <td>{s.data.lots.find((l) => l.id === o.lot)?.code}</td>
                  <td>{dateLabel(o.date)}</td>
                  <td>{dateLabel(o.due)}</td>
                  <td>{kg(o.kg)}</td>
                  <td>{kg(received(o))}</td>
                  <td>{kg(pending(o))}</td>
                </tr>
              ))}
            </Table>
          ),
        )}
      </Panel>
    </>
  );
}
