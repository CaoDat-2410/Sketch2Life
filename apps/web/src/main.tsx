import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import { authService } from "./modules/school-manager/be1/services/authService";
import "./shared/web-brand-theme.css";
import "./shared/portal-ui.css";
import "./shared/ui-primitives.css";
import "./shared/role-crayon-theme.css";
import "./shared/web-app.css";

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
