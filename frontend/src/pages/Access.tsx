import LanguageButton from "../components/LanguageButton";
import InvitationEntry from "../components/InvitationEntry";
import { locale, languageTags, translate } from "../lib/i18n";
import {
  invitationPath,
  invitationToken,
  isInvitationPage,
} from "../lib/invitationUrl";
import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { Action, Brand, Header, ThemeButton } from "../components/UI";
import { useDemo } from "../lib/session";
import { values } from "../lib/form";
export default function Access() {
  const s = useDemo(),
    loc = useLocation(),
    navigate = useNavigate(),
    invited = isInvitationPage(loc.pathname),
    token = invitationToken(loc.pathname, loc.search),
    invite = invited ? s.invited(token) : null;
  const [signup, setSignup] = useState(
      Boolean(invite && !invite.existingAccount),
    ),
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
            eyebrow={translate(
              invited ? "Invitación privada" : "Acceso a OriginLink",
            )}
            title={translate(
              invited
                ? invite
                  ? "Vincular mi cooperativa"
                  : "Acceso de proveedores"
                : signup
                  ? "Registrar tostadora"
                  : "Entra a tu espacio",
            )}
          >
            {invite && (
              <>
                {invite.name} {translate("invita a")} {invite.supplier}{" "}
                {translate("a compartir su catálogo.")}
              </>
            )}
          </Header>
          {invite && (
            <p className="muted">
              {translate("Enlace vigente hasta el")}{" "}
              {new Date(invite.expires).toLocaleDateString(
                languageTags[locale()],
              )}
            </p>
          )}
          {invited && !token ? (
            <>
              <p>
                {translate(
                  "Usa la invitación de una tostadora para crear tu cuenta de proveedor o vincular tu cuenta existente.",
                )}
              </p>
              <InvitationEntry />
              <Link to="/">{translate("Volver al inicio")}</Link>
            </>
          ) : invite && s.role ? (
            <div className="invite-link">
              {s.role === "cooperativa" ? (
                <button
                  onClick={() => {
                    if (s.acceptLink(token)) navigate("/", { replace: true });
                  }}
                >
                  {translate("Aceptar invitación")}
                </button>
              ) : (
                <p>
                  {translate(
                    "Para aceptar esta invitación, entra con una cuenta de proveedor.",
                  )}
                </p>
              )}
              <button className="quiet" onClick={s.switchAccount}>
                {translate("Usar otra cuenta")}
              </button>
            </div>
          ) : (
            translate(
              invited && !invite ? (
                <>
                  <p role="alert">
                    Invitación no válida. Pide una nueva a la tostadora.
                  </p>
                  <Link to="/">Volver al inicio</Link>
                </>
              ) : (
                <>
                  <form
                    key={String(signup) + token}
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
                          invited ? token : undefined,
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
                        <input
                          name="name"
                          defaultValue={invite?.supplier}
                          required
                          autoComplete="organization"
                        />
                      </label>
                    )}
                    <label>
                      Correo electrónico
                      <input
                        type="email"
                        name="email"
                        required
                        autoComplete="username"
                        defaultValue={invite?.email}
                      />
                    </label>
                    <label>
                      Contraseña
                      <input
                        type="password"
                        name="password"
                        autoComplete={
                          signup ? "new-password" : "current-password"
                        }
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
                          ? invited
                            ? "Crear cuenta de proveedor y aceptar"
                            : "Crear cuenta"
                          : invited
                            ? "Entrar y aceptar"
                            : "Iniciar sesión"}
                    </button>
                  </form>
                  {(!invited || !invite?.existingAccount) && (
                    <div className="access-actions">
                      <button
                        className="quiet"
                        onClick={() => {
                          setSignup(!signup);
                          setError("");
                        }}
                      >
                        {signup
                          ? "Ya tengo una cuenta"
                          : invited
                            ? "Crear cuenta de cooperativa"
                            : "Registrar una tostadora"}
                      </button>
                      {!invited && (
                        <Action secondary to={invitationPath("", locale())}>
                          Crear cuenta de proveedor o abrir invitación
                        </Action>
                      )}
                    </div>
                  )}
                </>
              ),
            )
          )}
          {translate(
            !invited && (
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
