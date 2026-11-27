import { useState } from "react";
import { locale, languageTags, type Locale } from "../lib/i18n";
export default function LanguageButton() {
  const [language, setLanguage] = useState(locale);
  return (
    <button
      type="button"
      className="quiet"
      aria-label={language === "es" ? "Switch to English" : "Cambiar a español"}
      onClick={() => {
        const next: Locale = language === "es" ? "en" : "es";
        localStorage.setItem("ol.language", next);
        document.documentElement.lang = languageTags[next];
        const url = new URL(location.href);
        if (next === "en") url.searchParams.set("lang", "en");
        else url.searchParams.delete("lang");
        history.replaceState(null, "", url);
        setLanguage(next);
        window.dispatchEvent(new Event("originlink-language"));
      }}
    >
      {language === "es" ? "EN" : "ES"}
    </button>
  );
}
