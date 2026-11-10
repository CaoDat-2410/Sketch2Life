import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/tokens.css";
import "./styles/parent-login-animation.css";
import "../../shared/parent-ui.css";
import "../../shared/ui-primitives.css";
import App from "./App";
import "../../shared/web-brand-theme.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
