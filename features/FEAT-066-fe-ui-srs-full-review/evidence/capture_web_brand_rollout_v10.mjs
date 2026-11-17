import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "web-brand-rollout-v10");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl);
if (!page?.webSocketDebuggerUrl) throw new Error("Loopback review browser page is unavailable.");

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
const evidence = { captures: [], limitations: ["Admin UI local preview not captured: required @tailwindcss/vite package is absent from the local npm cache; no network install or credentials used."] };
const viewports = [
  { name: "desktop", width: 1440, height: 900, mobile: false },
  { name: "narrow", width: 390, height: 844, mobile: true },
];

async function navigate(url) {
  await cdp("Page.navigate", { url });
  await delay(1100);
  await cdp("Runtime.evaluate", { expression: "window.scrollTo(0,0)" });
  await delay(350);
}
async function setThemeAndRole(role = null) {
  const roleScript = role
    ? `sessionStorage.setItem('s2l-web-role', ${JSON.stringify(role)});sessionStorage.setItem('s2l-web-authenticated','true');`
    : "sessionStorage.removeItem('s2l-web-role');sessionStorage.removeItem('s2l-web-authenticated');";
  await cdp("Runtime.evaluate", { expression: `localStorage.setItem('s2l-web-theme','light');localStorage.setItem('s2l-parent-theme','light');${roleScript}` });
  await cdp("Page.reload", { ignoreCache: true });
  await delay(1100);
}
async function inspect() {
  const result = await cdp("Runtime.evaluate", {
    expression: `({route:location.pathname+location.search,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,bodyBackground:getComputedStyle(document.body).backgroundColor,theme:getComputedStyle(document.documentElement).getPropertyValue('--color-paper').trim(),accent:getComputedStyle(document.documentElement).getPropertyValue('--color-accent').trim(),shell:document.querySelector('.mg-shell,.tw-shell,.stage')?.className??null,shellBackground:(()=>{const e=document.querySelector('.mg-shell,.tw-shell,.stage');return e?getComputedStyle(e).backgroundColor:null})(),logoImages:[...document.querySelectorAll('.s2l-brandmark,.login-scene__logo')].map(e=>({alt:e.alt||'',loaded:!!(e.complete&&e.naturalWidth),width:Math.round(e.getBoundingClientRect().width),height:Math.round(e.getBoundingClientRect().height)})),title:document.querySelector('h1,.mg-title,.tw-title')?.innerText?.trim()??document.title,overlay:!!document.querySelector('vite-error-overlay'),buttons:[...document.querySelectorAll('.mg-btn')].slice(0,6).map(e=>({text:e.innerText.trim(),height:Math.round(e.getBoundingClientRect().height),right:Math.round(e.getBoundingClientRect().right)}))})`,
    returnByValue: true,
  });
  return result.result?.result?.value ?? null;
}
async function capture(app, port, path, name, role = null) {
  const origin = `http://127.0.0.1:${port}`;
  await navigate(origin + path);
  await setThemeAndRole(role);
  if (role) await navigate(origin + path);
  for (const viewport of viewports) {
    await cdp("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
    await navigate(origin + path);
    const details = await inspect();
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const file = `${name}-${viewport.name}.png`;
    await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
    evidence.captures.push({ app, file, ...details });
  }
}

await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

await capture("School Manager", 5173, "/login", "school-manager-login");
await capture("School Manager", 5173, "/m02-organization-management", "school-manager-dashboard", "MANAGER");
await capture("School Manager", 5173, "/m01-publication-review", "school-manager-review", "MANAGER");
await capture("Teacher", 5172, "/login", "teacher-login");
await capture("Teacher", 5172, "/t01-lesson-workspace", "teacher-workspace", "TEACHER");
await capture("Platform Admin", 5174, "/login", "platform-admin-login");
await capture("Platform Admin", 5174, "/a02-platform-operations", "platform-admin-operations", "ADMIN");
await capture("Parent browser preview", 5175, "/p11-authentication", "parent-auth-redirect");
await capture("Parent browser preview", 5175, "/p01-lesson-library", "parent-library");

await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await navigate("http://127.0.0.1:5173/m02-organization-management");
await writeFile(join(outputDir, "observations.json"), JSON.stringify(evidence, null, 2), "utf8");
console.log(JSON.stringify({ outputDir, captureCount: evidence.captures.length, captures: evidence.captures, limitations: evidence.limitations }, null, 2));
socket.close();