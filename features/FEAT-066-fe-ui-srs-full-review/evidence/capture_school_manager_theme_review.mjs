import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const origin = "http://127.0.0.1:5173";
const evidenceDir = dirname(fileURLToPath(import.meta.url));
const outputDir = join(evidenceDir, "screenshots", "school-manager-theme-final");
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
        reject(new Error(`Timed out waiting for ${method}`));
      }
    }, 10000);
  });
}
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
await mkdir(outputDir, { recursive: true });
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Network.enable");
await cdp("Network.setBlockedURLs", { urls: ["https://*", "http://localhost:8000/*", "http://127.0.0.1:8000/*"] });
await cdp("Runtime.evaluate", { expression: "sessionStorage.clear()" });
await cdp("Page.navigate", { url: `${origin}/login` });
await delay(700);

const captures = [
  { name: "school-manager-login", route: "/login", viewports: ["desktop", "narrow"] },
  { name: "m02-dashboard", route: "/m02-organization-management", viewports: ["desktop", "narrow", "tablet"] },
  { name: "m02-teachers", route: "/m02-organization-management?section=teachers", viewports: ["desktop", "narrow"] },
  { name: "m02-classes", route: "/m02-organization-management?section=classes", viewports: ["desktop", "narrow", "tablet"] },
  { name: "m02-quota", route: "/m02-organization-management?section=quota", viewports: ["desktop", "narrow"] },
  { name: "m02-settings", route: "/m02-organization-management?section=settings", viewports: ["desktop", "narrow"] },
  { name: "m01-publication-review", route: "/m01-publication-review", viewports: ["desktop", "narrow"] },
];
const viewportByName = {
  desktop: { width: 1440, height: 900, mobile: false },
  narrow: { width: 390, height: 844, mobile: true },
  tablet: { width: 768, height: 1024, mobile: true },
};
const evidence = [];
for (const capture of captures) {
  if (capture.route !== "/login") {
    await cdp("Runtime.evaluate", {
      expression: "sessionStorage.setItem('s2l-web-role','MANAGER'); sessionStorage.setItem('s2l-web-authenticated','true')",
    });
  }
  for (const viewportName of capture.viewports) {
    const viewport = viewportByName[viewportName];
    await cdp("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.mobile,
    });
    await cdp("Page.navigate", { url: `${origin}${capture.route}` });
    await delay(650);
    await cdp("Runtime.evaluate", { expression: "window.scrollTo(0, 0)" });
    await delay(100);
    const inspection = await cdp("Runtime.evaluate", {
      expression: `({route:location.pathname+location.search, scrollY, viewport:{width:innerWidth,height:innerHeight}, documentWidth:document.documentElement.scrollWidth, horizontalOverflow:document.documentElement.scrollWidth>innerWidth, contentHeight:document.documentElement.scrollHeight, shellBackground:document.querySelector('.mg-shell')?getComputedStyle(document.querySelector('.mg-shell')).backgroundColor:null, inboxStatus:document.querySelector('.mg-inbox-unavailable')?.innerText??null, organizationContextTag:document.querySelector('.mg-org-context')?.tagName??null, activeNavigation:[...document.querySelectorAll('.mg-nav-item.is-active')].map(x=>x.innerText.trim()), tabs:[...document.querySelectorAll('[role=tab]')].map(x=>({id:x.id,controls:x.getAttribute('aria-controls'),selected:x.getAttribute('aria-selected'),tabIndex:x.tabIndex})), panels:[...document.querySelectorAll('[role=tabpanel]')].map(x=>({id:x.id,labelledby:x.getAttribute('aria-labelledby'),hidden:x.hidden})), disabledActions:[...document.querySelectorAll('.mg-btn:disabled')].map(x=>({text:x.innerText.trim(),minHeight:Math.round(x.getBoundingClientRect().height),left:Math.round(x.getBoundingClientRect().left),right:Math.round(x.getBoundingClientRect().right),insideViewport:x.getBoundingClientRect().left>=0&&x.getBoundingClientRect().right<=innerWidth})), tableScrollRegions:[...document.querySelectorAll('.mg-table-wrap')].map(x=>({clientWidth:x.clientWidth,scrollWidth:x.scrollWidth})), bodyText:document.body.innerText.slice(0,750)})`,
      returnByValue: true,
    });
    const details = inspection.result?.result?.value ?? null;
    const shot = await cdp("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: false });
    const fileName = `${capture.name}-${viewportName}.png`;
    await writeFile(join(outputDir, fileName), Buffer.from(shot.result.data, "base64"));
    evidence.push({ file: fileName, ...details });
  }
}
await writeFile(join(outputDir, "observations.json"), JSON.stringify(evidence, null, 2), "utf8");
console.log(JSON.stringify({ outputDir, screenshots: evidence.length, routes: [...new Set(evidence.map((item) => item.route))] }, null, 2));
socket.close();
