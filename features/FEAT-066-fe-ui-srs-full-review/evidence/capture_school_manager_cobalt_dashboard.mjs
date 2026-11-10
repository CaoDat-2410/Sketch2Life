import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const origin = "http://127.0.0.1:5173";
const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "school-manager-cobalt-preview");
const targets = await fetch("http://127.0.0.1:9233/json/list").then((response) => response.json());
const page = targets.find((target) => target.type === "page" && target.url.startsWith(origin));
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
    }, 10000);
  });
}
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
async function inspect() {
  const result = await cdp("Runtime.evaluate", {
    expression: "({route:location.pathname+location.search,viewport:{width:innerWidth,height:innerHeight},documentWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>innerWidth,shellClass:document.querySelector('.mg-shell')?.className??null,canvasToken:getComputedStyle(document.querySelector('.mg-shell')).getPropertyValue('--mg-canvas').trim(),shellBackground:getComputedStyle(document.querySelector('.mg-shell')).backgroundColor,accentToken:getComputedStyle(document.querySelector('.mg-shell')).getPropertyValue('--mg-accent').trim(),dashboardTitle:document.querySelector('.mg-title')?.innerText??null,inboxStatus:document.querySelector('.mg-inbox-unavailable')?.innerText??null,organizationContextTag:document.querySelector('.mg-org-context')?.tagName??null,actions:[...document.querySelectorAll('.mg-page.s2l-dashboard .mg-btn')].map(x=>({text:x.innerText.trim(),height:Math.round(x.getBoundingClientRect().height),insideViewport:x.getBoundingClientRect().right<=innerWidth}))})",
    returnByValue: true,
  });
  return result.result?.result?.value ?? null;
}
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await cdp("Runtime.evaluate", { expression: "sessionStorage.setItem('s2l-web-role','MANAGER');sessionStorage.setItem('s2l-web-authenticated','true')" });

const evidence = { captures: [], routeScope: [] };
for (const viewport of [
  { name: "desktop", width: 1440, height: 900, mobile: false },
  { name: "narrow", width: 390, height: 844, mobile: true },
]) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: viewport.width, height: viewport.height, deviceScaleFactor: 1, mobile: viewport.mobile });
  await cdp("Page.navigate", { url: origin + "/m02-organization-management" });
  await delay(700);
  await cdp("Runtime.evaluate", { expression: "window.scrollTo(0,0)" });
  await delay(100);
  const details = await inspect();
  const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
  const file = "m02-dashboard-" + viewport.name + ".png";
  await writeFile(join(outputDir, file), Buffer.from(shot.result.data, "base64"));
  evidence.captures.push({ file, ...details });
}

for (const route of [
  "/m02-organization-management?section=teachers",
  "/m01-publication-review",
]) {
  await cdp("Page.navigate", { url: origin + route });
  await delay(700);
  evidence.routeScope.push(await inspect());
}

await cdp("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await cdp("Page.navigate", { url: origin + "/m02-organization-management" });
await delay(700);
await writeFile(join(outputDir, "observations.json"), JSON.stringify(evidence, null, 2), "utf8");
console.log(JSON.stringify({ outputDir, captures: evidence.captures, routeScope: evidence.routeScope }, null, 2));
socket.close();
