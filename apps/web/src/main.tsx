import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import { authService } from "./modules/school-manager/be1/services/authService";
// One design system: tokens, then Tailwind utilities for shared/ui, then base, components, shell.
import "./shared/styles/tokens.css";
import "./shared/styles/tailwind-utilities.css";
import "./shared/styles/base.css";
import "./shared/styles/components.css";
import "./shared/styles/shell.css";
import "./shared/styles/koi-wave1.css";

window.sketch2lifeAuth = {
  signIn: async (email, password) => {
    await authService.login({ email, pass: password });
  },
  signOut: () => authService.logout(),
  getIdToken: () => authService.getIdToken(),
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
