import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "web-dashboard-icons-v11");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.url.startsWith("http://127.0.0.1:5173"));
if (!page?.webSocketDebuggerUrl) throw new Error("The local review browser page is unavailable.");

const socket = new WebSocket(page.webSocketDebuggerUrl);
const runtimeErrors = [];
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === "Runtime.exceptionThrown") runtimeErrors.push(message.params.exceptionDetails?.text ?? "runtime exception");
  if (message.method === "Log.entryAdded" && message.params.entry?.level === "error") runtimeErrors.push(message.params.entry.text);
  if (message.id === undefined) return;
  const callbacks = pending.get(message.id);
  if (!callbacks) return;
  pending.delete(message.id);
  if (message.error) callbacks.reject(new Error(message.error.message));
  else callbacks.resolve(message);
});
function cdp(method, params = {}) {
  const id = ++nextId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id);
        reject(new Error("Timed out waiting for " + method));
      }
    }, 12000);
  });
}
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
const viewports = [
  { name: "desktop", width: 1440, height: 900, mobile: false },
  { name: "narrow", width: 390, height: 844, mobile: true },
];
const apps = [
  { name: "school-manager", label: "School Manager", port: 5173, route: "/m02-organization-management", role: "MANAGER" },
  { name: "teacher", label: "Teacher", port: 5172, route: "/t01-lesson-workspace", role: "TEACHER" },
  { name: "platform-admin", label: "Platform Admin", port: 5174, route: "/a02-platform-operations", role: "ADMIN" },
];
const evidence = { baseline: "FEAT-066-EV-012 palette captures precede this icon refresh", captures: [], runtimeErrors, limitations: [] };

async function navigate(url) {
  await cdp("Page.navigate", { url });
  await delay(1000);
  await cdp("Runtime.evaluate", { expression: "window.scrollTo(0,0)" });
  await delay(250);
}
async function prepare(app) {
  const origin = "http://127.0.0.1:" + app.port;
  await navigate(origin + app.route);
  const role = JSON.stringify(app.role);
  await cdp("Runtime.evaluate", {
    expression: "localStorage.setItem('s2l-web-theme','light');sessionStorage.setItem('s2l-web-role'," + role + ");sessionStorage.setItem('s2l-web-authenticated','true')"
  });
  await cdp("Page.reload", { ignoreCache: true });
  await delay(1000);
}
async function inspect(app, viewport) {
  const expression = "({route:location.pathname+location.search,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,roleShell:document.querySelector('.mg-shell,.tw-shell')?.className??null,title:document.querySelector('h1,.mg-title,.tw-title')?.innerText?.trim()??document.title,errorOverlay:!!document.querySelector('vite-error-overlay'),navigation:[...document.querySelectorAll('.mg-nav-item,.tw-nav-item')].map(e=>({label:e.innerText.trim(),active:e.classList.contains('is-active')||e.classList.contains('is-on')})),iconCount:document.querySelectorAll('.mg-nav-ico svg,.mg-shell svg,.tw-shell svg').length,navIcon:(()=>{const e=document.querySelector('.mg-nav-item .mg-nav-ico,.tw-nav-item .mg-nav-ico');if(!e)return null;const s=getComputedStyle(e);return {width:Math.round(e.getBoundingClientRect().width),height:Math.round(e.getBoundingClientRect().height),cssWidth:s.width,display:s.display,background:s.backgroundColor,color:s.color,svgColor:getComputedStyle(e.querySelector('svg')).color,borderRadius:s.borderRadius}})()})";
  const result = await cdp("Runtime.evaluate", { expression, returnByValue: true });
  const details = result.result?.result?.value ?? null;
  if (details) details.runtimeErrors = runtimeErrors.slice();
  return details;
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Log.enable");
const captures = [];
for (const app of apps) {
  await prepare(app);
  for (const viewport of viewports) {
    await cdp("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
    await navigate("http://127.0.0.1:" + app.port + app.route);
    const details = await inspect(app, viewport);
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = app.name + "-dashboard-" + viewport.name + ".png";
    await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
    captures.push({ app: app.label, file, ...details });
  }
}
evidence.captures = captures;
evidence.runtimeErrors = runtimeErrors;
await writeFile(join(outputDir, "observations.json"), JSON.stringify(evidence, null, 2), "utf8");
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await navigate("http://127.0.0.1:5173/m02-organization-management");
console.log(JSON.stringify({ outputDir, captures, runtimeErrors, limitations: evidence.limitations }, null, 2));
socket.close();