import LanguageButton from "../components/LanguageButton";
import { locale, translate } from "../lib/i18n";
import { useState } from "react";
import { useLocation } from "react-router-dom";
import { Action, Brand, Header, ThemeButton } from "../components/UI";
import { useDemo } from "../lib/session";
import { values } from "../lib/form";

const supplierRegistrationPath = "/registro-proveedor";

export default function Access() {
  const s = useDemo(),
    supplierRegistration = useLocation().pathname === supplierRegistrationPath;
  const [signup, setSignup] = useState(supplierRegistration),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [roaster, R] = useState(
      s.demoRoasters.find((r) => r.id === 5)?.id ?? 3,
    ),
    [provider, P] = useState(s.demoSuppliers[0]?.id);
  return (
    <>
      <header className="top">
        <Brand />
        <span className="demo">{translate("Piloto · Datos simulados")}</span>
        <LanguageButton />
        <ThemeButton />
      </header>
      <main className="login" tabIndex={-1}>
        <section className="login-form">
          <Header
            eyebrow={translate("Acceso a OriginLink")}
            title={translate(
              supplierRegistration
                ? "Crear cuenta de proveedor"
                : signup
                  ? "Registrar tostadora"
                  : "Entra a tu espacio",
            )}
          />
          {translate(
            <>
              <form
                key={String(signup)}
                onSubmit={async (e) => {
                  e.preventDefault();
                  const v = values(e.currentTarget);
                  setError("");
                  setBusy(true);
                  try {
                    await s.credentials(
                      v.email,
                      v.password,
                      signup ? v.name : undefined,
                      supplierRegistration ? "cooperativa" : undefined,
                    );
                  } catch (ex) {
                    setError((ex as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {signup && (
                  <label>
                    Nombre de la organización
                    <input name="name" required autoComplete="organization" />
                  </label>
                )}
                <label>
                  Correo electrónico
                  <input
                    type="email"
                    name="email"
                    required
                    autoComplete="username"
                  />
                </label>
                <label>
                  Contraseña
                  <input
                    type="password"
                    name="password"
                    autoComplete={signup ? "new-password" : "current-password"}
                    minLength={signup ? 8 : undefined}
                    required
                  />
                </label>
                {signup && <small>Mínimo 8 caracteres.</small>}
                {error && <p role="alert">{error}</p>}
                <button disabled={busy}>
                  {busy
                    ? "Procesando…"
                    : signup
                      ? supplierRegistration
                        ? "Crear cuenta de proveedor"
                        : "Crear cuenta"
                      : "Iniciar sesión"}
                </button>
              </form>
              <div className="access-actions">
                {supplierRegistration ? (
                  <Action secondary to="/">
                    Ya tengo una cuenta
                  </Action>
                ) : (
                  <button
                    className="quiet"
                    onClick={() => {
                      setSignup(!signup);
                      setError("");
                    }}
                  >
                    {signup ? "Ya tengo una cuenta" : "Registrar una tostadora"}
                  </button>
                )}
                {!supplierRegistration && (
                  <Action
                    secondary
                    to={
                      supplierRegistrationPath +
                      (locale() === "en" ? "?lang=en" : "")
                    }
                  >
                    Crear cuenta de proveedor
                  </Action>
                )}
              </div>
            </>,
          )}
          {translate(
            !supplierRegistration && (
              <details className="demo-access">
                <summary>Probar con datos de demostración</summary>
                <label>
                  Tostadora
                  <select value={roaster} onChange={(e) => R(+e.target.value)}>
                    {s.demoRoasters.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button onClick={() => s.login("tostadora", roaster)}>
                  Entrar como tostadora →
                </button>
                <label>
                  Proveedor
                  <select value={provider} onChange={(e) => P(+e.target.value)}>
                    {s.demoSuppliers.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="secondary"
                  onClick={() => s.login("cooperativa", provider)}
                >
                  Entrar como cooperativa
                </button>
              </details>
            ),
          )}
          <p role="status">{translate(s.notice)}</p>
        </section>
        <aside className="login-art">
          <img alt={translate("")} src="/identidad/07-monocromo-blanco.svg" />
          <h2>
            {translate(" Tu abastecimiento, ")}
            <br />
            {translate(" en orden. ")}
          </h2>
          <p>
            {translate("Del lote de origen a la próxima jornada de tueste.")}
          </p>
        </aside>
      </main>
    </>
  );
}
