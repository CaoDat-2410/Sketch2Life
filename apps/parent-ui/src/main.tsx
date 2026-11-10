import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/tokens.css";
import "./styles/parent-login-animation.css";
import "../../shared/parent-ui.css";
import "../../shared/ui-primitives.css";
import "./styles/tablet.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
