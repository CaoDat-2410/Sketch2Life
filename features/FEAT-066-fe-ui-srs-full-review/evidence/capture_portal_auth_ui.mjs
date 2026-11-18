import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const phase = process.env.S2L_AUTH_CAPTURE_PHASE ?? "after";
const outputDir = join(evidenceDir, "screenshots", `auth-${phase}`);
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page");
if (!page?.webSocketDebuggerUrl) throw new Error("Isolated local Edge page is unavailable.");

const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.id === undefined) return;
  const task = pending.get(message.id);
  if (!task) return;
  pending.delete(message.id);
  clearTimeout(task.timeout);
  if (message.error) task.reject(new Error(message.error.message));
  else task.resolve(message);
});
function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, 12000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const response = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  if (response.result.exceptionDetails) throw new Error(response.result.exceptionDetails.text);
  return response.result.result.value;
}
const portals = [
  { id: "teacher", port: 5172 },
  { id: "school-manager", port: 5173 },
  { id: "platform-admin", port: 5174 },
];
const viewports = [
  { label: "desktop", width: 1440, height: 900, mobile: false },
  { label: "narrow", width: 390, height: 844, mobile: true },
];
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Network.setBlockedURLs", { urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"] });
const observations = [];

for (const portal of portals) {
  for (const viewport of viewports) {
    await cdp("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile,
    });
    const url = `http://127.0.0.1:${portal.port}/login`;
    await cdp("Page.navigate", { url });
    await new Promise((resolve) => setTimeout(resolve, 900));
    const details = await evaluate(`(() => ({
      title: document.title,
      route: location.pathname,
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      documentHeight: document.documentElement.scrollHeight,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
      headings: [...document.querySelectorAll("h1,h2")].map((node) => node.innerText),
      links: [...document.querySelectorAll("a")].map((node) => ({ text: node.innerText.trim(), href: node.href })),
      labels: [...document.querySelectorAll("label")].map((node) => node.innerText.trim()),
      form: {
        busy: document.querySelector("form")?.getAttribute("aria-busy"),
        inputTypes: [...document.querySelectorAll("form input")].map((input) => input.type),
        labels: [...document.querySelectorAll("form label")].map((label) => label.innerText.trim()),
        submitLabel: document.querySelector("form button[type=submit]")?.innerText.trim(),
        submitBottom: document.querySelector("form button[type=submit]")?.getBoundingClientRect().bottom ?? null
      },
      roleNavigation: {
        label: document.querySelector("nav")?.getAttribute("aria-label"),
        currentRole: document.querySelector("nav [aria-current=page]")?.innerText.trim() ?? null,
        destinationCount: document.querySelectorAll("nav a[href]").length,
        unavailableCount: document.querySelectorAll("nav [aria-disabled=true]").length,
        minimumTouchHeight: Math.min(...[...document.querySelectorAll("nav a, nav [aria-disabled=true]")].map((node) => Math.round(node.getBoundingClientRect().height)))
      },
      scene: {
        webglReady: document.querySelector(".s2l-auth-webgl")?.classList.contains("is-ready") ?? false,
        canvasWidth: document.querySelector(".s2l-auth-webgl")?.width ?? null,
        canvasHeight: document.querySelector(".s2l-auth-webgl")?.height ?? null,
        canvasAccessible: document.querySelector(".s2l-auth-webgl")?.getAttribute("aria-hidden") === "true",
        reducedMotion: matchMedia("(prefers-reduced-motion: reduce)").matches,
        animationState: document.querySelector(".s2l-auth-scene-host")?.dataset.animation ?? null,
        fallbackVisibility: getComputedStyle(document.querySelector(".s2l-auth-art-fallback")).visibility
      },
      text: document.body.innerText.slice(0, 700)
    }))()`);
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = `${portal.id}-${viewport.label}.png`;
    await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
    observations.push({ portal: portal.id, viewport: viewport.label, file, ...details });
  }
}
await writeFile(join(outputDir, "observations.json"), JSON.stringify({
  phase,
  source: "isolated headless Edge; only loopback Vite apps; HTTPS requests blocked; no credentials submitted",
  observations,
}, null, 2) + "\n");
socket.close();
console.log(JSON.stringify(observations, null, 2));