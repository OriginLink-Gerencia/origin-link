import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useDemo } from "../lib/session";
export function Brand() {
  return (
    <span className="brand">
      <img
        className="horizontal"
        src="/identidad/01-horizontal.svg"
        alt="OriginLink"
      />
      <span className="compact">
        <img src="/identidad/03-isotipo.svg" alt="OriginLink" />
      </span>
      <span className="inverse">
        <img src="/identidad/07-monocromo-blanco.svg" alt="OriginLink" />
        <span className="brand-name" aria-hidden="true">OriginLink</span>
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
      <small>{eyebrow}</small>
      <h1>{title}</h1>
      {children && <p>{children}</p>}
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
      {children}
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
      <h2>{title}</h2>
      {children}
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
            {labels.map((x) => (
              <th scope="col" key={x}>
                {x}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
export function ThemeButton() {
  const s = useDemo();
  return (
    <button className="quiet" aria-pressed={s.theme} onClick={s.toggleTheme}>
      {s.theme ? "Tema claro" : "Tema oscuro"}
    </button>
  );
}
