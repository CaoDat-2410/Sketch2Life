import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const nm = (pkg: string) => fileURLToPath(new URL(`./node_modules/${pkg}`, import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "react/jsx-runtime": nm("react/jsx-runtime.js"),
      "react/jsx-dev-runtime": nm("react/jsx-dev-runtime.js"),
      "react-dom/client": nm("react-dom/client.js"),
      react: nm("react"),
      "react-dom": nm("react-dom"),
      "react-router-dom": nm("react-router-dom"),
      "@radix-ui/react-dialog": nm("@radix-ui/react-dialog"),
      "@radix-ui/react-accordion": nm("@radix-ui/react-accordion"),
    },
  },
});
