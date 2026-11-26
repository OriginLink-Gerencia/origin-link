import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { locale, translate } from "../lib/i18n";
import { invitationPath, parseInvitation } from "../lib/invitationUrl";

export default function InvitationEntry() {
  const navigate = useNavigate();
  const [error, setError] = useState(false);
  return (
    <form
      className="invite-link"
      onSubmit={(event) => {
        event.preventDefault();
        const input = new FormData(event.currentTarget).get("invitation");
        const token = parseInvitation(String(input ?? ""));
        setError(!token);
        if (token) navigate(invitationPath(token, locale()));
      }}
    >
      <label>
        {translate("Enlace o código de invitación")}
        <input
          name="invitation"
          required
          autoCapitalize="none"
          spellCheck={false}
          aria-invalid={error}
          onChange={() => setError(false)}
        />
      </label>
      {error && (
        <p role="alert">
          {translate("Pega un enlace o código de invitación válido.")}
        </p>
      )}
      <button type="submit" className="secondary">
        {translate("Abrir invitación")}
      </button>
    </form>
  );
}
