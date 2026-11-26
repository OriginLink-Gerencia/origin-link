import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import "./controls.css";

const preference =
  new URL(location.href).searchParams.get("lang") ??
  localStorage.getItem("ol.language") ??
  "es";
document.documentElement.lang = preference === "en" ? "en-US" : "es-PE";
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
