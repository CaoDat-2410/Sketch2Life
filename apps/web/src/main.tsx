import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import "./shared/web-brand-theme.css";
import "./shared/portal-ui.css";
import "./shared/ui-primitives.css";
import "./shared/role-crayon-theme.css";
import "./shared/web-app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
