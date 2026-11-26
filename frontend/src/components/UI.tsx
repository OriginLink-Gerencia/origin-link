import { translate } from "../lib/i18n";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useDemo } from "../lib/session";
export function Brand() {
  return (
    <span className="brand">
      <img
        className="horizontal"
        src="/identidad/01-horizontal.svg"
        alt={translate("OriginLink")}
      />
      <span className="compact">
        <img src="/identidad/03-isotipo.svg" alt={translate("OriginLink")} />
      </span>
      <span className="inverse">
        <img
          src="/identidad/07-monocromo-blanco.svg"
          alt={translate("OriginLink")}
        />
        <span className="brand-name" aria-hidden="true">
          {translate("OriginLink")}
        </span>
      </span>
    </span>
  );
}
export function Header({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <header className="heading">
      <small>{translate(eyebrow)}</small>
      <h1>{translate(title)}</h1>
      {translate(children && <p>{children}</p>)}
    </header>
  );
}
export function Action({
  to,
  children,
  secondary = false,
}: {
  to: string;
  children: ReactNode;
  secondary?: boolean;
}) {
  return (
    <Link className={"button " + (secondary ? "secondary" : "")} to={to}>
      {translate(children)}
    </Link>
  );
}
export function Panel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      <h2>{translate(title)}</h2>
      {translate(children)}
    </section>
  );
}
export function Table({
  labels,
  children,
}: {
  labels: string[];
  children: ReactNode;
}) {
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>
            {translate(
              labels.map((x) => (
                <th scope="col" key={x}>
                  {x}
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>{translate(children)}</tbody>
      </table>
    </div>
  );
}
export function ThemeButton() {
  const s = useDemo();
  return (
    <button className="quiet" aria-pressed={s.theme} onClick={s.toggleTheme}>
      {translate(s.theme ? "Tema claro" : "Tema oscuro")}
    </button>
  );
}
