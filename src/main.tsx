import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { loadCatalog } from "./lib/catalog";
import "./styles/global.css";
import "./styles/ui.css";

const root = createRoot(document.getElementById("root")!);

// The formations catalogue lives in PostgreSQL: load it before the first render.
loadCatalog()
  .then(() => root.render(<StrictMode><App /></StrictMode>))
  .catch(() =>
    root.render(
      <div style={{ padding: 48, fontFamily: "sans-serif" }}>
        <h1>Le serveur est injoignable</h1>
        <p>Le catalogue des formations n’a pas pu être chargé depuis la base de données.</p>
        <button onClick={() => location.reload()}>Réessayer</button>
      </div>,
    ),
  );
