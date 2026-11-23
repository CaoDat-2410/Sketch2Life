import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import { authService } from "./modules/school-manager/be1/services/authService";
import "./shared/styles/web-brand-theme.css";
import "./shared/styles/portal-ui.css";
import "./shared/styles/ui-primitives.css";
import "./shared/styles/role-crayon-theme.css";
import "./shared/styles/web-app.css";
import "./shared/styles/sketch2life-theme.css";
import "./shared/styles/cozy-shell.css";

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
